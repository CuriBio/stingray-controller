// adapted from https://github.com/talk-to/vue-components/blob/master/src/index.js
// export { default as Waveform } from "./components/waveform/Waveform.vue";

// Why don't you export default?
// https://humanwhocodes.com/blog/2019/01/stop-using-default-exports-javascript-module/

// Pure JS
export { convertFromJsonOfSampleIdxAndValue } from "./js-utils/WaveformDataFormatter";
export { getWellSliceToDisplay } from "./js-utils/WaveformDataFormatter";
export { getArraySliceToDisplay } from "./js-utils/WaveformDataFormatter";
export { convertFromJsonOfWellIndicesAndXYArrays } from "./js-utils/WaveformDataFormatter";
export { appendWellData } from "./js-utils/WaveformDataFormatter";
export { WellTitle } from "./js-utils/LabwareCalculations";
export { TextValidation } from "./js-utils/TextValidation";

// Store
export { default as settingsStoreModule } from "./store/modules/settings";
export { default as systemStoreModule } from "./store/modules/system";
export { default as stimulationStoreModule } from "./store/modules/stimulation";
export {
  STIM_STATUS,
  MAX_SUBPROTOCOL_DURATION_MS,
  MIN_SUBPROTOCOL_DURATION_MS,
  MIN_CHARGE_MA,
  MIN_PHASE_DURATION_US,
  MAX_CHARGE_MA,
} from "./store/modules/stimulation/enums";
export { SYSTEM_STATUS } from "./store/modules/system/enums";

// Basic Widgets
export { default as PlateWell } from "./components/basic-widgets/PlateWell.vue";
export { default as InputWidget } from "./components/basic-widgets/InputWidget.vue";
export { default as ButtonWidget } from "./components/basic-widgets/ButtonWidget.vue";
export { default as InputDropDown } from "./components/basic-widgets/InputDropDown.vue";
export { default as SelectDropDown } from "./components/basic-widgets/SelectDropDown.vue";
export { default as CheckBoxWidget } from "./components/basic-widgets/CheckBoxWidget.vue";
export { default as StimulationStudioPlateWell } from "./components/stimulation/StimulationStudioPlateWell.vue";

// Settings related
export { default as SettingsButton } from "./components/settings/SettingsButton.vue";
export { default as SettingsForm } from "./components/settings/SettingsForm.vue";

// Status Related
export { default as StatusBar } from "./components/status/StatusBar.vue";
export { default as SimulationMode } from "./components/status/SimulationMode.vue";
export { default as ErrorCatchWidget } from "./components/status/ErrorCatchWidget.vue";
export { default as StatusWarningWidget } from "./components/status/StatusWarningWidget.vue";
export { default as StatusSpinnerWidget } from "./components/status/StatusSpinnerWidget.vue";
export { default as StimQCSummary } from "./components/status/StimQCSummary.vue";
export { default as BarcodeViewer } from "./components/status/BarcodeViewer.vue";

// Stimulation Studio
export { default as StimulationStudioCreateAndEdit } from "./components/stimulation/StimulationStudioCreateAndEdit.vue";
export { default as StimulationStudioDragAndDropPanel } from "./components/stimulation/StimulationStudioDragAndDropPanel.vue";
export { default as StimulationStudioBlockViewEditor } from "./components/stimulation/StimulationStudioBlockViewEditor.vue";
export { default as StimulationStudioWaveformSettingModal } from "./components/stimulation/StimulationStudioWaveformSettingModal.vue";
export { default as StimulationStudioDelayModal } from "./components/stimulation/StimulationStudioDelayModal.vue";
export { default as StimulationStudioProtocolViewer } from "./components/stimulation/StimulationStudioProtocolViewer.vue";
export { default as StimulationStudioWaveform } from "./components/stimulation/StimulationStudioWaveform.vue";
export { default as StimulationStudioZoomControls } from "./components/stimulation/StimulationStudioZoomControls.vue";
export { default as StimulationStudio } from "./components/stimulation/StimulationStudio.vue";
export { default as StimulationStudioWidget } from "./components/stimulation/StimulationStudioWidget.vue";
export { default as StimulationStudioControls } from "./components/stimulation/StimulationStudioControls.vue";
