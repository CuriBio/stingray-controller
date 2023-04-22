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
  getProtocolName({ protocolEditor }) {
    return protocolEditor.name;
  },
  getRestDuration({ protocolEditor }) {
    return protocolEditor.restDuration;
  },
};

export const getProtocolEditorLetter = (list) => {
  const protocolIdx = list.length - 1;
  const letterAssignment = ALPHABET[protocolIdx % 26];
  const numLetters = Math.floor(protocolIdx / 26) + 1;

  return letterAssignment.repeat(numLetters);
};
