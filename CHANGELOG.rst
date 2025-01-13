Changelog for Stingray Controller
=================================


0.4.5 (unreleased)
------------------

Added:
^^^^^^
- Better handling of errors during Stimulation Configuration Check

Changed:
^^^^^^^^
- Stim pulse images

Fixed:
^^^^^^
- Issue with deletion of one stim protocol resulting in deletion of other stim protocols


0.4.4 (2024-07-17)
------------------

Changed:
^^^^^^^^
- Serial buffer size is now 1MB


0.4.3 (2024-04-29)
------------------

Added:
^^^^^^
- Biphasic stim check


0.4.2 (2024-02-12)
------------------

Fixed:
^^^^^^
- Dropdown overflow styling
- Initial barcode read after reconnecting to an instrument in offline mode will no longer stop stimulation
- Barcode change warning now displays in the correct position
- Barcode change while stimulating now correctly requires another stim configuration check before restarting stimulation


0.4.1 (2024-02-06)
------------------

Added:
^^^^^^
- Compatibility with new FW update procedure in cloud

Fixed:
^^^^^^
- Issue restarting stim after re-entering online mode
- Well selection is no longer editable in stim studio while stim is running
- Running stim checks and starting stim are no longer able to be performed when an invalid barcode is present


0.4.0 (2023-09-12)
------------------

Added:
^^^^^^
- Offline mode
- Support for barcodes of MA Mini Plates
- Handling for new firmware error reporting

Fixed:
^^^^^^
- Stim start/stop button will turn into a spinner while waiting for stim to start/stop


0.3.0 (2023-07-11)
------------------

Added:
^^^^^^
- Ability to loop subprotocols in stimulation studio
- Backwards stimulation protocol compatibility

Changed:
^^^^^^^^
- Minimum phase duration is now 25μs instead of 20μs

Fixed:
^^^^^^
- Error message for when:

  - The instrument's firmware is incompatible with the software
  - An error occurs during software install


0.2.0 (2023-06-05)
------------------

Added:
^^^^^^
- Offline FW updating
- Protocol validation checks on import in Stimulation Studio
- Disabled sidebar controls before connection to instrument is made

Changed:
^^^^^^^^
- Error codes
- New login flow

Fixed:
^^^^^^
- SW auto-updating
- Issue with firmware versions always reported as being incompatible
- Prevent connection to Mantarray instruments


0.1.0 (2023-04-13)
------------------

Added:
^^^^^^
- Initial repo setup
