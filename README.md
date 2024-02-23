# sd-danbooru-tags-upsampler

日本語は[こちら](./README-ja.md)へ

An extension for Stable Diffusion Web UI that upsamples prompts by generating or completing danbooru tags using lightweight LLM.

It's useful for people who don't want think about long prompt or want to see **diverse**, **natural** and **high quality** images without any thinking.

## Usage

<img src="./images/screenshot-1.jpg" width="540px" alt="Scrennshot of this extension" />

Open the `Danbooru Tags Upsampler` accordion and check the `Enable` checkbox to enable this extension.

Explanation of parameters:

| Parameter name | Description | Example value |
| -------------- | ----------- | ------------- |
| **Total tag length** | This parameter can specify the amount of **total tags after completing the positive prompt**. Not the amount of completing tags. `very short` means "less than 10 tags", `short` means "less than 20 tags", `long` means "less than 40 tags" and `very long` is more than that. | `long` is recommended |
| **Ban tags** | All tags in this field will never appear in completion tags. It's useful when you don't want to contain some specific tags. | `official alternate costume, english text, animal focus, ...` |
| **Seed for upsampling tags** | If this number and the positive prompt are fixed, the completion tags are also fixed. `-1` means "generates tags using random seed every time" | If you want to generate images with different final prompts every time, set to `-1`. |
| **Upsampling timing** | When to upsample, before or after styles are applied. | `Before applying styles` |

## Showcaases

<table>
    <tr>
        <td width="30%">Input prompt</td>
        <td width="30%"><b>Without</b> upsampling</td>
        <td width="30%"><b>With</b> upsampling</td>
    </tr>
    <tr>
        <td>1girl, solo, cowboy shot (seed: 2396487241)</td>
        <td>
            <img src="./images/sample-1-wo.jpg" alt="Sample image 1 generated without upsampling" />
        </td>
        <td><img src="./images/sample-1-w.jpg" alt="Sample image 1 generated with upsampling" /></td>
    </tr>
    <tr>
        <td>(prompts used to generate) </td>
        <td><b>1girl, solo, cowboy shot</b></td>
        <td><b>1girl, solo, cowboy shot, ahoge, animal ears, bare shoulders, blue hair, blush, closed mouth, collarbone, collared shirt, dress, eyelashes, fox ears, fox girl, fox tail, hair between eyes, heart, long hair, long sleeves, looking at viewer, neck ribbon, ribbon, shirt, simple background, sleeves past wrists, smile, tail, white background, white dress, white shirt, yellow eyes</b></td>
    </tr>
    <tr>
        <td>3girls (seed: 684589178)</td>
        <td>
            <img src="./images/sample-2-wo.jpg" alt="Sample image 2 generated without upsampling" />
        </td>
        <td><img src="./images/sample-2-w.jpg" alt="Sample image 2 generated with upsampling" /></td>
    </tr>
    <tr>
        <td>(prompts used to generate) </td>
        <td><b>3girls</b></td>
        <td><b>3girls, black footwear, black hair, black thighhighs, boots, bow, bowtie, chibi, closed mouth, collared shirt, flower, grey hair, hair between eyes, hair flower, hair ornament, long hair, long sleeves, looking at viewer, multiple girls, purple eyes, red eyes, shirt, short hair, sitting, smile, thighhighs, vest, white shirt, white skirt</b></td>
    </tr>
    <tr>
        <td>no humans, scenery (seed: 3702717413)</td>
        <td>
            <img src="./images/sample-3-wo.jpg" alt="Sample image 3 generated without upsampling" />
        </td>
        <td><img src="./images/sample-3-w.jpg" alt="Sample image 3 generated with upsampling" /></td>
    </tr>
    <tr>
        <td>(prompts used to generate) </td>
        <td><b>no humans, scenery</b></td>
        <td><b>no humans, scenery, animal, animal focus, bird, blue eyes, cat, dog, flower, grass, leaf, nature, petals, shadow, sitting, star (sky), sunflower, tree</b></td>
    </tr>
    <tr>
        <td>1girl, frieren, sousou no frieren
 (seed: 787304393)</td>
        <td>
            <img src="./images/sample-4-wo.jpg" alt="Sample image 4 generated without upsampling" />
        </td>
        <td><img src="./images/sample-4-w.jpg" alt="Sample image 4 generated with upsampling" /></td>
    </tr>
    <tr>
        <td>(prompts used to generate) </td>
        <td><b>1girl, frieren, sousou no frieren</b></td>
        <td><b>1girl, frieren, sousou no frieren, black pantyhose, cape, closed mouth, elf, fingernails, green eyes, grey hair, hair between eyes, long hair, long sleeves, looking at viewer, pantyhose, pointy ears, simple background, skirt, solo, twintails, white background, white skirt</b></td>
    </tr>
</table>


Generation settings:

- Model: [AnimagineXL 3.0](https://huggingface.co/cagliostrolab/animagine-xl-3.0)
- Negative prompt (same as the recommended settings of animaginexl 3.0):

```
nsfw, lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, artist name
```

Upsampling settings:

- Total tag length: `long`
- Ban tags: none
- Seed: `-1`
- When to perform the process: `Before applying styles`

## Access to the model weights

This extension uses the following model:

- `p1atdev/dart-v1-sft`: [🤗 HuggingFace](https://huggingface.co/p1atdev/dart-v1-sft)

## Acknowledgements

This project has been influenced by the following projects and researches. We express our respect and gratitude to the developers and contributors of these projects:

- succinctly/text2image-prompt-generator: https://huggingface.co/succinctly/text2image-prompt-generator
- Gustavosta/MagicPrompt-Stable-Diffusion: https://huggingface.co/Gustavosta/MagicPrompt-Stable-Diffusion
- FredZhang7/anime-anything-promptgen-v2: https://huggingface.co/FredZhang7/anime-anything-promptgen-v2
- sd-dynamic-prompts: https://github.com/adieyal/sd-dynamic-prompts
- DALL-E 3: https://cdn.openai.com/papers/dall-e-3.pdf
- caption-upsampling: https://github.com/sayakpaul/caption-upsampling
- StableDiffusionWebUI: https://github.com/AUTOMATIC1111/stable-diffusion-webui and its derivatives
