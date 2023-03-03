// adapted from https://github.com/talk-to/vue-components/blob/master/src/index.js
// export { default as Waveform } from "./components/waveform/Waveform.vue";

// Why don't you export default?
// https://humanwhocodes.com/blog/2019/01/stop-using-default-exports-javascript-module/

// Pure JS
export { convert_from_json_of_sample_idx_and_value } from "./js_utils/waveform_data_formatter";
export { get_well_slice_to_display } from "./js_utils/waveform_data_formatter";
export { get_array_slice_to_display } from "./js_utils/waveform_data_formatter";
export { convert_from_json_of_well_indices_and_x_y_arrays } from "./js_utils/waveform_data_formatter";
export { append_well_data } from "./js_utils/waveform_data_formatter";
export { WellTitle } from "./js_utils/labware_calculations";
export { TextValidation } from "./js_utils/text_validation";

// Store
export { default as settings_store_module } from "./store/modules/settings";
export { default as flask_store_module } from "./store/modules/flask";
export { system_status_regexp, all_mantarray_commands_regexp } from "./store/modules/flask/url_regex";
export { default as stimulation_store_module } from "./store/modules/stimulation";
export {
  stimStatus,
  MAX_SUBPROTOCOL_DURATION_MS,
  MIN_SUBPROTOCOL_DURATION_MS,
} from "./store/modules/stimulation/enums";
export { STATUS as FLASK_STATUS_ENUMS } from "./store/modules/flask/enums";

export { default as create_web_socket_plugin } from "./store/plugins/websocket";
export { socket } from "./store/plugins/websocket";

export { default as BarcodeViewer } from "./components/playback/controls/BarcodeViewer.vue";
export { default as StimulationControls } from "./components/playback/controls/StimulationControls.vue";

// Basic Widgets
export { default as PlateWell } from "./components/basic_widgets/PlateWell.vue";
export { default as InputWidget } from "./components/basic_widgets/InputWidget.vue";
export { default as ButtonWidget } from "./components/basic_widgets/ButtonWidget.vue";
export { default as InputDropDown } from "./components/basic_widgets/InputDropDown.vue";
export { default as SelectDropDown } from "./components/basic_widgets/SelectDropDown.vue";
export { default as CheckBoxWidget } from "./components/basic_widgets/CheckBoxWidget.vue";
export { default as RadioButtonWidget } from "./components/basic_widgets/RadioButtonWidget.vue";
export { default as StimulationStudioPlateWell } from "./components/basic_widgets/StimulationStudioPlateWell.vue";
export { default as ToggleWidget } from "./components/basic_widgets/ToggleWidget.vue";

// Plate Based
export { default as StimulationStudioWidget } from "./components/plate_based_widgets/stimulationstudio/StimulationStudioWidget.vue";

// Status Related
export { default as StatusBar } from "./components/status/StatusBar.vue";
export { default as RecordingTime } from "./components/status/RecordingTime.vue";
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
