"""Display selected experimental TEM frames; no segmentation or measurements."""
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image


def main():
    project = Path(__file__).resolve().parent
    data = project / 'data' / 'public_tem_series' / 'kang_2021'
    indices = [26, 63, 101, 118, 135]
    fig, axes = plt.subplots(2, 3, figsize=(12, 8), layout='constrained')
    for ax, index in zip(axes.flat, indices):
        with Image.open(data / f'movie_s1_frame_{index:03d}.png') as source:
            frame = np.array(source)
        ax.imshow(frame, interpolation='nearest')
        ax.set_title(f'Experimental movie S1: frame {index}')
        ax.axis('off')
    axes.flat[-1].axis('off')
    axes.flat[-1].text(0.05, 0.8,
        'Read the timestamps printed in the images.\n\n'
        'Movie playback is faster than acquisition.\n\n'
        'These are decoded, drift-corrected movie frames.\n'
        'Particle motion and imaging noise are both visible.\n\n'
        'Source: Kang et al. (2021), CC BY-NC 4.0.',
        transform=axes.flat[-1].transAxes, va='top', fontsize=10)
    fig.suptitle('Actual liquid-cell TEM: compare the same field across time')
    fig.savefig(project / 'experimental_tem_series_preview.png', dpi=150)
    plt.show()


if __name__ == '__main__':
    main()
