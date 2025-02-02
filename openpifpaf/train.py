"""Train a pifpaf network."""

import argparse
import datetime
import socket

import torch

from . import datasets, encoder, logs, optimize, transforms
from .network import losses, nets, Trainer
from . import __version__ as VERSION
import torchvision.models as models

def default_output_file(args):
    out = 'outputs/{}-{}'.format(args.basenet, '-'.join(args.headnets))
    if args.square_edge != 321:
        out += '-edge{}'.format(args.square_edge)
    if args.regression_loss != 'laplace':
        out += '-{}'.format(args.regression_loss)
    if args.r_smooth != 0.0:
        out += '-rsmooth{}'.format(args.r_smooth)
    if args.dilation:
        out += '-dilation{}'.format(args.dilation)
    if args.dilation_end:
        out += '-dilationend{}'.format(args.dilation_end)

    now = datetime.datetime.now().strftime('%y%m%d-%H%M%S')
    out += '-{}.pkl'.format(now)

    return out


def cli():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    logs.cli(parser)
    nets.cli(parser)
    losses.cli(parser)
    encoder.cli(parser)
    optimize.cli(parser)
    datasets.train_cli(parser)

    parser.add_argument('-o', '--output', default=None,
                        help='output file')
    parser.add_argument('--stride-apply', default=1, type=int,
                        help='apply and reset gradients every n batches')
    parser.add_argument('--epochs', default=75, type=int,
                        help='number of epochs to train')
    parser.add_argument('--freeze-base', default=0, type=int,
                        help='number of epochs to train with frozen base')
    parser.add_argument('--pre-lr', type=float, default=1e-4,
                        help='pre learning rate')
    parser.add_argument('--update-batchnorm-runningstatistics',
                        default=False, action='store_true',
                        help='update batch norm running statistics')
    parser.add_argument('--square-edge', default=401, type=int,
                        help='square edge of input images')
    parser.add_argument('--lambdas', default=[30.0, 2.0, 2.0, 50.0, 3.0, 3.0],
                        type=float, nargs='+',
                        help='prefactor for head losses')
    parser.add_argument('--ema', default=1e-3, type=float,
                        help='ema decay constant')
    parser.add_argument('--debug-without-plots', default=False, action='store_true',
                        help='enable debug but dont plot')
    parser.add_argument('--profile', default=None,
                        help='enables profiling. specify path for chrome tracing file')
    parser.add_argument('--disable-cuda', action='store_true',
                        help='disable CUDA')
    parser.add_argument('--no-augmentation', dest='augmentation',
                        default=True, action='store_false',
                        help='do not apply data augmentation')
    args = parser.parse_args()

    if args.output is None:
        args.output = default_output_file(args)

    if args.debug and 'skeleton' not in args.headnets:
        raise Exception('add "skeleton" as last headnet to see debug output')

    if args.debug_without_plots:
        args.debug = True

    # add args.device
    args.device = torch.device('cpu')
    args.pin_memory = False
    if not args.disable_cuda and torch.cuda.is_available():
        args.device = torch.device('cuda')
        args.pin_memory = True

    return args


def main():
    args = cli()
    logs.configure(args)
    net_cpu, start_epoch = nets.factory_from_args(args)    
        
    #temp = models.alexnet(pretrained=False)  
    # TODO: understand why this was here. This part seems to be used for no pretrained model training?
    # temp = torch.load("./outputs/3d-resnet50.pkl")['model']
    # print(temp)
    # print(net_cpu)
    # print(net_cpu.base_net)
    # net_cpu.base_net = temp
    # print(net_cpu)
    # sys.exit(0)
        
    # load pretrained basenet and pifpaf headnet if i have not declared a checkpoint
    if(args.checkpoint is None):
        print("loading pretrained basenet and pifpaf headnets")
        pretrained = torch.load("./outputs/resnet50-pifpaf-trained.pkl")['model']
        net_cpu.base_net = pretrained.base_net
        net_cpu.head_nets[0] = pretrained.head_nets[0]
        net_cpu.head_nets[1] = pretrained.head_nets[1]
        #net_cpu.head_nets[2] = pretrained.head_nets[2]
    
    for head in net_cpu.head_nets:
        head.apply_class_sigmoid = False

    net = net_cpu.to(device=args.device)
    if not args.disable_cuda and torch.cuda.device_count() > 1:
        print('Using multiple GPUs: {}'.format(torch.cuda.device_count()))
        net = torch.nn.DataParallel(net)

    optimizer, lr_scheduler = optimize.factory(args, net.parameters())
    loss = losses.factory_from_args(args)
    target_transforms = encoder.factory(args, net_cpu.io_scales())
    target_transforms = target_transforms[:-1]

    if args.augmentation:
        preprocess = transforms.Compose([
            transforms.HFlip(0.5),
            transforms.RescaleRelative(),
            transforms.Crop(args.square_edge),
            transforms.CenterPad(args.square_edge),
        ])
    else:
        preprocess = transforms.Compose([
            transforms.RescaleAbsolute(args.square_edge),
            transforms.CenterPad(args.square_edge),
        ])
        
    # load datasets
    # ======================================================================================================
    coco_train_loader, coco_val_loader, coco_pre_train_loader, \
    jaad_train_loader, jaad_val_loader, jaad_pre_train_loader = datasets.train_factory(args, preprocess, target_transforms, jaad_datasets=[args.jaad_train, args.jaad_val, args.jaad_pre_train])
    train_loader = [coco_train_loader, jaad_train_loader]
    val_loader = [coco_val_loader, jaad_val_loader]
    pre_train_loader = [coco_pre_train_loader, jaad_pre_train_loader]
    # ======================================================================================================

    encoder_visualizer = None
    if args.debug and not args.debug_without_plots:
        encoder_visualizer = encoder.Visualizer(args.headnets, net_cpu.io_scales())

    if args.freeze_base:
        print("Haha I was freezing all along")
        # freeze base net parameters
        frozen_params = set()
        for n, p in net.named_parameters():
            # Freeze only base_net parameters.
            # Parameter names in DataParallel models start with 'module.'.
            if not n.startswith('module.base_net.') and \
               not n.startswith('base_net.'):
                print('not freezing', n)
                continue
            print('freezing', n)
            if p.requires_grad is False:
                continue
            p.requires_grad = False
            frozen_params.add(p)
        print('froze {} parameters'.format(len(frozen_params)))

        # training
        foptimizer = torch.optim.SGD(
            (p for p in net.parameters() if p.requires_grad),
            lr=args.pre_lr, momentum=0.9, weight_decay=0.0, nesterov=True)
        ftrainer = Trainer(net, loss, foptimizer, args.output,
                           device=args.device, fix_batch_norm=True,
                           encoder_visualizer=encoder_visualizer)
        for i in range(-args.freeze_base, 0):
            ftrainer.train(pre_train_loader, i)

        # unfreeze
        for p in frozen_params:
            p.requires_grad = True
            
        # save epoch 0
        ftrainer.write_model(0, False)       

    trainer = Trainer(
        net, loss, optimizer, args.output,
        lr_scheduler=lr_scheduler,
        device=args.device,
        fix_batch_norm=not args.update_batchnorm_runningstatistics,
        stride_apply=args.stride_apply,
        ema_decay=args.ema,
        encoder_visualizer=encoder_visualizer,
        train_profile=args.profile,
        model_meta_data={
            'args': vars(args),
            'version': VERSION,
            'hostname': socket.gethostname(),
        },
    )
    trainer.loop(train_loader, val_loader, args.epochs, start_epoch=start_epoch)


if __name__ == '__main__':
    main()
