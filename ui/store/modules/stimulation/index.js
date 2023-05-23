import mutations from "./mutations";
import { default as getters, getDefaultProtocolEditorState } from "./getters";
import actions from "./actions";
import { STIM_STATUS } from "./enums";

const state = () => ({
  selectedWells: [],
  protocolList: [{ letter: "", color: "", label: "Create New" }],
  protocolAssignments: {},
  protocolEditor: getDefaultProtocolEditorState(),
  currentAssignment: { letter: "", color: "" },
  xAxisValues: [],
  yAxisValues: [],
  repeatColors: [],
  yAxisScale: 120,
  delayBlocks: [],
  xAxisUnitName: "milliseconds",
  stimPlayState: false,
  xAxisTimeIdx: 0,
  editMode: { status: false, protocol: "", label: "", color: "" },
  stimStatus: STIM_STATUS.NO_PROTOCOLS_ASSIGNED,
  hoveredPulses: [],
  stimulatorCircuitStatuses: [],
  invalidImportedProtocols: []
});

export default {
  namespaced: true,
  state,
  mutations,
  getters,
  actions,
  STIM_STATUS
};
