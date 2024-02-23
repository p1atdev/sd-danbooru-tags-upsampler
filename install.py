import launch

if not launch.is_installed("onnxruntime"):
    launch.run_pip(
        "install optimum[onnxruntime]", "requirements for Danbooru Tags Upsampler"
    )
