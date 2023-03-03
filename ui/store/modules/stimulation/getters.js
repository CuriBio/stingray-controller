import { COLOR_PALETTE, ALPHABET } from "./enums";
// eslint-disable-next-line require-jsdoc
export function getDefaultProtocolEditorState() {
  return {
    name: "",
    runUntilStopped: true,
    stimulationType: "C",
    restDuration: 0,
    timeUnit: "milliseconds",
    subprotocols: [],
    detailedSubprotocols: [],
  };
}
export default {
  getProtocols({ protocolList }) {
    return protocolList;
  },
  getNextProtocol(state) {
    const { protocolList } = state;

    if (!state.editMode.status) {
      const letter = getProtocolEditorLetter(protocolList);
      const color = COLOR_PALETTE[protocolList.length % 26];
      state.currentAssignment = { letter, color };
      return { color, letter };
    } else if (state.editMode.status) {
      return state.currentAssignment;
    }
  },
  getStimulationType({ protocolEditor }) {
    return protocolEditor.stimulationType === "C" ? "Current" : "Voltage";
  },

  getProtocolName({ protocolEditor }) {
    return protocolEditor.name;
  },
  getRestDuration({ protocolEditor }) {
    return protocolEditor.restDuration;
  },
};

const getProtocolEditorLetter = (list) => {
  const protocol_idx = list.length - 1;
  const letter_assignment = ALPHABET[protocol_idx % 26];
  const num_letters = Math.floor(protocol_idx / 26) + 1;

  return letter_assignment.repeat(num_letters);
};
