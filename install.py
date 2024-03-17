import launch

if not launch.is_installed("optimum"):
    launch.run_pip(
        "install optimum[onnxruntime]", "requirements for Danbooru Tags Upsampler"
    )


if not launch.is_installed("onnxruntime"):
    launch.run_pip(
        "install optimum[onnxruntime]", "requirements for Danbooru Tags Upsampler"
    )


if launch.is_installed("tensorflow"):
    show_result = launch.run(
        f'"{launch.python}" -m pip show tensorflow',
    )
    if "2.15.1" not in show_result:
        launch.run_pip(
            "install -U tensorflow==2.15.1",
            "tensorflow for Danbooru Tags Upsampler to avoid the error with transformers==4.30.2",
        )
