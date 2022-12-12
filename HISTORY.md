# History
## Krita Plugin
### 1.3.4
Changes
- The generated images are now transferred via Cloudflare r2.

### 1.3.3
Changes
- The new parameter r2 is transferred with value False. This disables for now the new Cloudflare r2 image download.

### 1.3.2
Changes
- Now detailed error messages are displayed. Before only the standard HTTP error messages.

### 1.3.1
Changes
- In the case no worker is available for image generation, now a message is displayed.
- Minimum size has been reduced from 512x512 to 384x384.

Bugfixes
- In the dialog init strength selector was not disabled in mode inpainting.
- In the dialog in mode inpainting was not checked if a layer with an inpainting image exists.

### 1.3.0
Changes
- Inpainting is supported now.

### 1.2.0
Changes
- Now images with sizes between 512x512 and 1024x1024 can be generated. Before only 512x512.
- The dialog has now two tabs to make the layout cleaner.
- It is now checked, if support for webp in Qt5 exists. On some Linux distributions the support is missing and needs to be installed manually.

### 1.1.1
Bugfixes
- When using img2img in some cases an error 400 occurred.
- It was not checked, if a prompt was entered. If it was missing, an error 400 occurred.

### 1.1.0
Changes
- img2img is now supported.

Bugfixes
- If the dialog was closed via the cross, the generation was not stopped.

### 1.0.1
Changes
- Now status information is displayed after generation start.

### 1.0.0
- Initial version.
