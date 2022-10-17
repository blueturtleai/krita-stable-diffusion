# krita-stable-diffusion

This repository includes a Krita plugin for communication with [stablehorde](https://stablehorde.net). Stablehorde is a cluster of stable-diffusion servers run by volunteers. You can create stable-diffusion images for free without running a colab notebook or a local server. Please check the section "Limitations" to better understand where the limits are.

Please check HISTORY.md for the latest changes. 

## Installation
### Krita

The plugin has been tested in Krita 5.1.1.

1. Download the [Krita plugin zip](https://github.com/blueturtleai/krita-stable-diffusion/releases/download/v1.0.0/krita_stablehorde_1_0_0.zip).

2. Start Krita and open the "Tools/Scripts/Import Python Plugin from File" menu and select the downloaded zip. Restart Krita.

3. You should see now the new menu item "Tools/Scripts/Stablehorde". If this is not the case, something went wrong.

## Generate images
Now we are ready for generating images.

1. Start Krita and create a new document with a minimum size of 512x512 and a paint layer.

2. Select the new "Tools/Scripts/Stablehorde" menu item. A dialog will open, where you can enter the details for the image generation.

   - **Prompt Strength:** How much the AI should follow the prompt. The higher the value, the more the AI will generate an image which looks like your prompt. 8 is a good value to use.

   - **Steps:** How many steps the AI should use to generate the image. The higher the value, the more the AI will work on details. But it also means, the longer the generation takes and the more the GPU is used. 50 is a good value to use.

   - **Seed:** This parameter is optional. If it is empty, a random seed will be generated on the server. If you use a seed, the same image is generated again in the case the same parameters for init strength, steps, etc. are used. A slightly different image will be generated, if the parameters are modified. You find the seed as part of the layer name of the layer, where the generated image is displayed. 

   - **NSFW:** If you want to send a prompt, which is excplicitly NSFW (Not Safe For Work). If you flag your request as NSFW, only servers, which accept NSFW prompts, work on the request. It's very likely, that it takes then longer than usual to generate the image. If you don't flag the prompt, but it is NSFW, you will receive a black image.

   - **Prompt:** How the generated image should look like.

   - **API key:** This parameter is optional. If you don't enter an API key, you run the image generation as anonymous. The downside is, that you will have then the lowest priority in the generation queue. For that reason it is recommended registering for free on [stablehorde](https://stablehorde.net) and getting an API key.

   - **Max Wait:** The maximum time in minutes you want to wait until image generation is finished. When the max time is reached, a timeout happens and the generation request is stopped.

   - **Generate:** Start image generation. The values you inserted into the dialog will be transmitted to the server, which dispatches the request now to one of the stable-diffusion servers in the cluster. Your generation request is added to the queue. You will see now the status "Waiting for generated image..." and all input elements of the dialog are disabled. When the image has been generated successfully, it will be shown as a new layer of the opened document. The used seed is shown as a part of the name of the new layer. If an error during generation occurs, the error message will be shown in the status textarea and all input elements will be enabled again.

   - **Cancel:** Close the dialog. If you cancel when you already started generation, generation will be stopped.

## Limitations

   - **Stability:** Stablehorde is still pretty new and under heavy development. So, it's not unlikely, that the servers are not available for some time or unexpected errors occur.

   - **Image size:** Currently only 512x512 is possible. In general stablehorde can also generate larger images, but not all servers in the cluster are able to do this. To make sure, that your images are generated as fast as possible, the plugin currently generates only 512x512. As soon as there are more servers in the cluster, which support larger images, it will be possible to generate larger sizes.

   - **Generation speed:** Stablehorde is a cluster of stable-diffusion servers run by volunteers. The generation speed depends on how many servers are in the cluster, which hardware they use and how many others want to generate with stablehorde. The upside is, that stablehorde is free to use, the downside that the generation speed is unpredictable.

   - **Privacy:** The privacy stablehorde offers is similar to generating in a public discord channel. So, please assume, that neither your prompts nor your generated images are private.
   
   - **Features:** Currently only text2img is available. As soon as stablehorde supports img2img and in-/out-painting, this will be available in the plugin too.

## FAQ

**Will Img2img, In- and Out-Painting be supported?** Very likely everything will be supported. This depends on which features the stablehorde cluster supports.

**How do I report an error or request a new feature?** Please open a new issue in this repository.
