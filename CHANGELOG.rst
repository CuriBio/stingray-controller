Changelog for Stingray Controller
=================================

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
