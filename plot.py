"""
Example command: 
python plot.py --exp=nbody-n4 --method=none
"""

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import tqdm

import argparse
import os
import pickle

parser = argparse.ArgumentParser(description='GNN_dropout')
parser.add_argument('--multi_plot', type=bool, default=True,  
                    help='Plot 10 different test cases')
parser.add_argument('--single_plot', type=bool, default=False,  
                    help='Plot trajectory for single idx')
parser.add_argument('--exp', type=str, default='pendulum-n2',  
                    help='experiment name')
parser.add_argument('--method', type=str, default='dropout', 
                    help='Use dropout, vi, or none')
parser.add_argument('--animate', type=bool, default=True, 
                    help='produce animation plots')
parser.add_argument('--idx', type=int, default=1, 
                    help='Choose which trajectory to animate')
parser.add_argument('--dropout_rate', type=float, default=0.5, 
                    help='dropout rate used just for naming plots. Not used if method is vi')
# parser.add_argument('--frames', type=int, default=200, 
#                     help='frames for animation plot. Can just use runs of simulations')


plt.rcParams['figure.figsize'] = (8, 6)
plt.rcParams['figure.dpi'] = 300

plt.rcParams.update({
    'font.size': 17,
})


args = parser.parse_args()
multi_plot=args.multi_plot
exp = args.exp
method = args.method 
dropout_rate = args.dropout_rate
animate = args.animate
# frames=args.frames
idx=args.idx

# Setting used for animation
num_samples = 100

# setting dropout rate and save dir
if method == 'dropout':
    save_dir = f'./results/{exp}/{method}_{dropout_rate}/'
else:
    dropout_rate = 0.
    save_dir = f'./results/{exp}/{method}/'

if not os.path.exists(save_dir):
    os.makedirs(save_dir)

# Load pkl file called all_traj.pkl

with open(f'{save_dir}all_traj.pkl', 'rb') as f:
    all_traj = pickle.load(f)



# Function to plot a single trajectory
def plot_paths(all_traj, idx):
    trajectories = all_traj[idx]

    r = trajectories['actual_pos']
    for i in range(r.shape[1]):
        plt.plot(r[:,i,0], r[:,i,1], '-', color=f'C{i}', alpha=0.2)
    # plt.plot(r[-1,:,0], r[-1,:,1], 'o', color='black', alpha=0.1)

    r = trajectories['pred_pos'][0]
    for i in range(r.shape[1]):
        plt.plot(r[:,i,0], r[:,i,1], '-', color=f'C{i}', alpha=1.)
    plt.plot(r[-1,:,0], r[-1,:,1], 'o', color='black', alpha=1.)

# Plot a single trajectory idx and save it
if args.single_plot:
    plot_paths(all_traj, idx)
    # plt.show()
    plt.savefig(save_dir + f'trajectory_{idx}.png')

## Using the list all_traj, generate a single figure with 10 subplots, each showing the trajectories of the 10 test cases.
## Figure should arrange subplots in a squarish grid.
## Use the plot_paths function to generate each subplot.
## Add a title to each subplot showing the test case number.
if multi_plot:

    factor = len(all_traj) // 5
    fig, axs = plt.subplots(5, factor, figsize=(5 * factor, 20))
    axs = axs.flatten()

    for idx, ax in enumerate(axs):
        ax.set_aspect('equal', adjustable='box')
        plt.sca(ax)
        plot_paths(all_traj, idx)
        plt.title(f"Test Case {idx+1}")

    plt.tight_layout()
    # plt.show()

    ## Save the figure as a pdf file.

    fig.savefig(save_dir + f'sample_{5 * factor}_trajectories.png')

# Animate plots

if animate:
    
    for idx in range(min(len(all_traj), 10)):
        
        trajectories = all_traj[idx]
        frames = trajectories['pred_pos_avg'].shape[0]

        fig, ax = plt.subplots()

        r = trajectories['pred_pos_avg']
        traj_pred = [ax.plot(r[:,i,0], r[:,i,1], '-', color=f'C{i}', alpha=1.)[0] for i in range(r.shape[1])]  
        ball_pred, = ax.plot(r[-1,:,0], r[-1,:,1], 'o', color='black', alpha=0.5, zorder=5.)
        if 'pendulum' in exp:
            rods_pred, = ax.plot([0] + list(r[-1,:,0]), [0] + list(r[-1,:,1]), '-', color='gray', alpha=1.)
        else:
            rods_pred, = ax.plot([], [], '-', color='gray', alpha=1.)

        r = trajectories['pred_pos']
        point_cloud = [ax.plot(r[:,0,i,0], r[:,0,i,1], 'o', color=f'C{i}', 
                            alpha=5. / num_samples, zorder=4., markerfacecolor=None)[0] 
                    for i in range(r.shape[2])]  

        def gather():
            return point_cloud + traj_pred + [rods_pred, ball_pred]

        def init():
            ax.set_aspect('equal', adjustable='box')
            if 'pendulum' in exp:
                lim = 1.03 * trajectories['pred_pos_avg'].shape[1]
                ax.set_xlim(-lim, lim)
                ax.set_ylim(-lim, lim)
            return gather()

        def update(frame):
            
            r = trajectories['pred_pos_avg']
            for i in range(r.shape[1]):
                traj_pred[i].set_data([], [])
            ball_pred.set_data(r[frame,:,0], r[frame,:,1])
            if 'pendulum' in exp:
                rods_pred.set_data([0] + list(r[frame,:,0]), [0] + list(r[frame,:,1]))
            
            r = trajectories['pred_pos']
            for i in range(r.shape[2]):
                point_cloud[i].set_data(r[:,frame,i,0], r[:,frame,i,1])
            
            return gather()

        ani = FuncAnimation(fig, update, frames=tqdm.trange(frames), init_func=init, blit=True, interval=20)
        writergif = PillowWriter(fps=30, bitrate=1000) 
        ani.save(save_dir + f'animation_{idx}.gif', writer=writergif)