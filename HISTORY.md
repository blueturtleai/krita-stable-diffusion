# History
## Krita Plugin
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
