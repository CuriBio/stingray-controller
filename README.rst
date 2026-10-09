Stingray 96 Controller
======================

Firmware Updates
----------------

The Stingray 96 Controller does not download software or firmware updates from the cloud.

- **Software updates:** uninstall the current version, then download and install the new version.
- **Firmware updates:** the controller checks a local directory for firmware files every time it boots up.

To install a firmware update, place the firmware file(s) in the ``firmware_updates`` folder inside the
controller's application data directory before launching the controller. On Windows this is::

    %APPDATA%\Stingray 96 Controller\firmware_updates\

Files must be named ``<firmware type>-<version>.bin``, where the firmware type is either ``main`` or
``channel`` and the version is a semantic version, for example ``main-1.2.3.bin`` or ``channel-2.0.0.bin``.
Files that do not follow this naming scheme are ignored and a warning is written to the controller log.

On boot up, if a file contains a newer version than the firmware currently on the instrument, the user is
prompted to install it. Channel firmware is installed before main firmware if both are present. A file is
deleted after its firmware has been installed successfully. There is no compatibility check between the
firmware files and the controller version, so make sure the firmware being distributed is compatible with the
controller version it is being installed with.
