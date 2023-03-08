// adapted from https://github.com/talk-to/vue-components/blob/master/src/index.js
// export { default as Waveform } from "./components/waveform/Waveform.vue";

// Why don't you export default?
// https://humanwhocodes.com/blog/2019/01/stop-using-default-exports-javascript-module/

// Pure JS
export { convert_from_json_of_sample_idx_and_value } from "./js-utils/WaveformDataFormatter";
export { get_well_slice_to_display } from "./js-utils/WaveformDataFormatter";
export { get_array_slice_to_display } from "./js-utils/WaveformDataFormatter";
export { convert_from_json_of_well_indices_and_x_y_arrays } from "./js-utils/WaveformDataFormatter";
export { append_well_data } from "./js-utils/WaveformDataFormatter";
export { WellTitle } from "./js-utils/LabwareCalculations";
export { TextValidation } from "./js-utils/TextValidation";

// Store
export { default as settings_store_module } from "./store/modules/settings";
export { default as system_store_module } from "./store/modules/system";
export { default as stimulation_store_module } from "./store/modules/stimulation";
export {
  stimStatus,
  MAX_SUBPROTOCOL_DURATION_MS,
  MIN_SUBPROTOCOL_DURATION_MS,
} from "./store/modules/stimulation/enums";
export { STATUS as SYSTEM_STATUS_ENUMS } from "./store/modules/system/enums";

export { default as create_web_socket_plugin } from "./store/plugins/websocket";
export { socket } from "./store/plugins/websocket";

export { default as BarcodeViewer } from "./components/status/BarcodeViewer.vue";
export { default as StimulationStudioControls } from "./components/stimulation/StimulationStudioControls.vue";

// Basic Widgets
export { default as PlateWell } from "./components/basic-widgets/PlateWell.vue";
export { default as InputWidget } from "./components/basic-widgets/InputWidget.vue";
export { default as ButtonWidget } from "./components/basic-widgets/ButtonWidget.vue";
export { default as InputDropDown } from "./components/basic-widgets/InputDropDown.vue";
export { default as SelectDropDown } from "./components/basic-widgets/SelectDropDown.vue";
export { default as CheckBoxWidget } from "./components/basic-widgets/CheckBoxWidget.vue";
export { default as StimulationStudioPlateWell } from "./components/stimulation/StimulationStudioPlateWell.vue";

// Settings related
export { default as AddUser } from "./components/settings/AddUser.vue";
export { default as EditUser } from "./components/settings/EditUser.vue";
export { default as SettingsButton } from "./components/settings/SettingsButton.vue";
export { default as SettingsForm } from "./components/settings/SettingsForm.vue";

// Status Related
export { default as StatusBar } from "./components/status/StatusBar.vue";
export { default as SimulationMode } from "./components/status/SimulationMode.vue";
export { default as ErrorCatchWidget } from "./components/status/ErrorCatchWidget.vue";
export { default as StatusWarningWidget } from "./components/status/StatusWarningWidget.vue";
export { default as StatusSpinnerWidget } from "./components/status/StatusSpinnerWidget.vue";
export { default as StimQCSummary } from "./components/status/StimQCSummary.vue";

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
