"""Run PaddleOCR's tools/train.py with one change that full text lines need.

In training mode the PP-OCRv6 recognition backbone pools its feature map to a
fixed 40 columns (`F.adaptive_avg_pool2d(x, [1, 40])` in rec_lcnetv4.py). That
suits the 320 px word crops the model was trained on, but our images are whole
printed lines, 1280 px wide with about 70 characters: 40 columns cannot spell
them, so the pretrained model starts at near-zero accuracy in training mode
while scoring over 99 % in evaluation mode. Here the training pass uses the
same pooling as evaluation (`F.avg_pool2d(x, [3, 2])`), which keeps one column
per 8 px of line width. It requires a fixed 48 px training height.

Second change: BatchNorm layers keep their pretrained running statistics
instead of re-estimating them from each batch. With batches of 8 padded line
images the batch statistics are too noisy (the pretrained model drops from
100 % to about 87 % character similarity on a clean batch).

    cd work/PaddleOCR && python ../../finetune/train_lines.py -c <config.yml>
"""
import runpy
import sys

import paddle.nn.functional as F


class _LinePooling:
    """paddle.nn.functional, except for the fixed-width training pool."""

    def __getattr__(self, name):
        return getattr(F, name)

    @staticmethod
    def adaptive_avg_pool2d(x, output_size, *args, **kwargs):
        if list(output_size) == [1, 40]:
            return F.avg_pool2d(x, [3, 2])
        return F.adaptive_avg_pool2d(x, output_size, *args, **kwargs)


def patch():
    sys.path.insert(0, ".")
    import ppocr.modeling.backbones.rec_lcnetv4 as backbone
    backbone.F = _LinePooling()

    import paddle
    import ppocr.modeling.architectures as arch
    build = arch.build_model

    def build_frozen_bn(config):
        model = build(config)
        for layer in model.sublayers():
            if isinstance(layer, (paddle.nn.BatchNorm, paddle.nn.BatchNorm1D, paddle.nn.BatchNorm2D)):
                layer._use_global_stats = True
        return model

    arch.build_model = build_frozen_bn


if __name__ == "__main__":
    patch()
    runpy.run_path("tools/train.py", run_name="__main__")
