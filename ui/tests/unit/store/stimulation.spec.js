import Vuex from "vuex";
import { createLocalVue } from "@vue/test-utils";
import { COLOR_PALETTE, STIM_STATUS, ALPHABET } from "@/store/modules/stimulation/enums";
import {
  VALID_STIM_JSON,
  INVALID_STIM_JSON,
  TEST_PROTOCOL_LIST,
  TEST_PROTOCOL_ORDER,
  INCOMPATIBLE_PROTOCOL_EXPORT_MULTI,
} from "@/tests/sample-stim-protocols/stim-protocols";

describe("store/stimulation", () => {
  const localVue = createLocalVue();
  localVue.use(Vuex);
  let NuxtStore;
  let store;
  const testWells = {
    SELECTED: [true, true, false, false, false],
    UNSELECTED: [false, true, false, false, false],
  };

  describe("stimulation/getters", () => {
    beforeAll(async () => {
      const storePath = `${process.env.buildDir}/store.js`;
      NuxtStore = await import(storePath);
    });

    beforeEach(async () => {
      store = await NuxtStore.createStore();
      store.state.stimulation.protocolList = JSON.parse(JSON.stringify(TEST_PROTOCOL_LIST));
    });

    test("When the protocol dropdown displays available protocols, Then only only protocols with defined label should return", async () => {
      const protocols = store.getters["stimulation/getProtocols"];
      const labeledProtocols = store.state.stimulation.protocolList.filter(
        (protocol) => protocol.label.length != 0
      ).length;
      expect(protocols).toHaveLength(labeledProtocols);
    });
    test("When requesting the next available protocol assignment(color, letter), Then the protocol received should be unused and unique", async () => {
      store.state.stimulation.protocolList = [{ letter: "", color: "", label: "Create New" }];

      [...Array(26)].map((_, i) => {
        const { color, letter } = store.getters["stimulation/getNextProtocol"];

        store.state.stimulation.protocolList.push({ color, letter });
        expect(color).toBe(COLOR_PALETTE[i % 26 === 25 ? 0 : (i % 26) + 1]);
      });

      // expect that double letters will be chosen after initial 26 are used as single characters
      // reuse color palette every 26
      [...Array(26)].map((_, i) => {
        const { color, letter } = store.getters["stimulation/getNextProtocol"];
        store.state.stimulation.protocolList.push({ color, letter });
        expect(color).toBe(COLOR_PALETTE[i % 26 === 25 ? 0 : (i % 26) + 1]);
        expect(letter).toBe(ALPHABET[i] + ALPHABET[i]);
      });
      // just ensure it continues to add a letter
      [...Array(26)].map((_, i) => {
        const { color, letter } = store.getters["stimulation/getNextProtocol"];

        store.state.stimulation.protocolList.push({ color, letter });

        expect(color).toBe(COLOR_PALETTE[i % 26 === 25 ? 0 : (i % 26) + 1]);
        expect(letter).toBe(ALPHABET[i] + ALPHABET[i] + ALPHABET[i]);
      });
    });

    test("When there are no saved protocols, Then the letter assigned to new protocol will be A", async () => {
      store.state.stimulation.protocolList = [{ letter: "", color: "", label: "Create New" }];
      const { letter } = await store.getters["stimulation/getNextProtocol"];
      expect(letter).toBe("A");
    });

    test("When a protocol is selected to be editted, Then the letter and color assignment should be that of the selected protocol", async () => {
      const selectedProtocol = store.state.stimulation.protocolList[1];
      await store.dispatch("stimulation/editSelectedProtocol", selectedProtocol);

      const { letter, color } = store.getters["stimulation/getNextProtocol"];

      expect(letter).toBe("A");
      expect(color).toBe("#118075");
    });

    test("When requesting the name and rest duration to edit existing protocol in the editor, Then it should return specified pulse order", async () => {
      const selectedProtocol = store.state.stimulation.protocolList[1];
      const { name, restDuration } = selectedProtocol.protocol;
      await store.dispatch("stimulation/editSelectedProtocol", selectedProtocol);

      const actualName = store.getters["stimulation/getProtocolName"];
      expect(actualName).toBe(name);

      const actualDelay = store.getters["stimulation/getRestDuration"];
      expect(actualDelay).toBe(restDuration);
    });
    test("When protocol file has been read and contains now invalid values, Then the protocol names will be added to state to show to user", async () => {
      const parsedStimData = JSON.parse(INVALID_STIM_JSON);
      await store.dispatch("stimulation/addImportedProtocol", parsedStimData);

      expect(store.state.stimulation.invalidImportedProtocols).toStrictEqual([
        "testProto_1",
        "testProto_2",
        "testProto_3",
      ]);
    });
    test("Given a protocol has been selected for edit, When requesting the protocol assignment in the protocol editor, Then it should return the assignment of the selected protocol for edit", async () => {
      const selectedProtocol = store.state.stimulation.protocolList[1];
      const { letter, color } = selectedProtocol;
      const expectedAssignment = { letter, color };
      await store.dispatch("stimulation/editSelectedProtocol", selectedProtocol);
      const defaultType = store.getters["stimulation/getNextProtocol"];
      expect(defaultType).toStrictEqual(expectedAssignment);
    });
  });
  describe("stimulation/mutations/actions", () => {
    beforeAll(async () => {
      const storePath = `${process.env.buildDir}/store.js`;
      NuxtStore = await import(storePath);
    });

    beforeEach(async () => {
      store = await NuxtStore.createStore();
      store.state.stimulation.protocolList = JSON.parse(JSON.stringify(TEST_PROTOCOL_LIST));
    });
    afterEach(() => {
      jest.resetAllMocks();
    });

    test("When stimulation store is initialized, Then default selected wells should be an empty array", () => {
      const { selectedWells } = store.state.stimulation;
      expect(selectedWells).toStrictEqual([]);
    });

    test("When stimulation store is mutated to add or remove selected wells, Then selected wells in state should update according to wells", () => {
      store.dispatch("stimulation/handleSelectedWells", testWells.SELECTED);
      expect(store.state.stimulation.selectedWells).toStrictEqual([0, 1]);

      store.dispatch("stimulation/handleSelectedWells", testWells.UNSELECTED);
      expect(store.state.stimulation.selectedWells).toStrictEqual([1]);
    });

    test("When stimulation store is mutated with a new protocol name, Then said name should update in state", () => {
      const name = "TestName";
      store.commit("stimulation/setProtocolName", name);
      expect(store.state.stimulation.protocolEditor.name).toBe(name);
    });

    test("When stimulation store is mutated with a new delay frequency, Then said frequency should update in state", () => {
      const delay = "10";
      const intDelay = 10;
      store.commit("stimulation/setRestDuration", delay);
      expect(store.state.stimulation.protocolEditor.restDuration).toBe(intDelay);
    });

    test("When a user adds a protocol to selected wells, Then the selected wells should be added to protocol assignments with specified protocol", async () => {
      const testAssignment = {
        0: { letter: "B", color: "#45847b", label: "test_B" },
        1: { letter: "B", color: "#45847b", label: "test_B" },
      };
      const { protocolList } = store.state.stimulation;
      protocolList.push(testAssignment[0]);
      await store.dispatch("stimulation/handleSelectedWells", testWells.SELECTED);
      await store.commit("stimulation/applySelectedProtocol", protocolList[2]);

      expect(store.state.stimulation.protocolAssignments).toStrictEqual(testAssignment);
      expect(store.state.stimulation.stimStatus).toBe(STIM_STATUS.CONFIG_CHECK_NEEDED);
    });
    test("When changes the stim studios x-axis unit, Then the coordinate values in the store will be changed accordingly", async () => {
      const testMsCoordinates = {
        xValues: [0, 5000, 10000, 15000],
        yValues: [50, 55, 60, 65],
      };
      const testSecCoordinates = {
        xValues: [0, 5, 10, 15],
        yValues: [50, 55, 60, 65],
      };

      const msObj = { idx: 0, unitName: "milliseconds" };
      const secObj = { idx: 1, unitName: "seconds" };

      await store.commit("stimulation/setAxisValues", testMsCoordinates);

      await store.dispatch("stimulation/handleXAxisUnit", secObj);
      expect(store.state.stimulation.xAxisValues).toStrictEqual(testSecCoordinates.xValues);
      expect(store.state.stimulation.yAxisValues).toStrictEqual(testSecCoordinates.yValues);

      // test to ensure it won't happen twice in a row, will only occur when the index value is changed
      await store.dispatch("stimulation/handleXAxisUnit", secObj);
      expect(store.state.stimulation.xAxisValues).toStrictEqual(testSecCoordinates.xValues);
      expect(store.state.stimulation.yAxisValues).toStrictEqual(testSecCoordinates.yValues);

      await store.dispatch("stimulation/handleXAxisUnit", msObj);
      expect(store.state.stimulation.xAxisValues).toStrictEqual(testMsCoordinates.xValues);
      expect(store.state.stimulation.yAxisValues).toStrictEqual(testMsCoordinates.yValues);

      // test to ensure it won't happen twice in a row, will only occur when the index value is changed
      await store.dispatch("stimulation/handleXAxisUnit", msObj);
      expect(store.state.stimulation.xAxisValues).toStrictEqual(testMsCoordinates.xValues);
      expect(store.state.stimulation.yAxisValues).toStrictEqual(testMsCoordinates.yValues);
    });

    test("When a user imports a new protocol file, Then it will be read by the FileReader API and dispatched", async () => {
      const file = {
        name: "test.json",
        size: 450,
        type: "application/json",
      };

      const reader = {
        readAsText: jest.fn(),
        onload: jest.fn(),
        onerror: jest.fn(),
        result: VALID_STIM_JSON,
      };
      jest.spyOn(global, "FileReader").mockImplementation(() => reader);
      await store.dispatch("stimulation/handleImportProtocol", file);
      reader.onload();
      reader.onerror();
      expect(reader.readAsText).toHaveBeenCalledTimes(1);
    });

    test("When a user clicks to export current protocol, Then json document will be downloaded locally", async () => {
      window.webkitURL.createObjectURL = function () {};
      const mockCreateElement = jest.spyOn(document, "createElement");

      await store.dispatch("stimulation/handleExportProtocol");
      expect(mockCreateElement).toHaveBeenCalledTimes(1);
      expect(mockCreateElement).toHaveBeenCalledWith("a");

      window.URL.createObjectURL = function () {};
      window.webkitURL = null;

      await store.dispatch("stimulation/handleExportProtocol");
      expect(mockCreateElement).toHaveBeenCalledTimes(2);
    });

    test("When protocol file has been read, Then it will be given a new color/letter assignment and added to protocol list in state", async () => {
      const parsedStimData = JSON.parse(VALID_STIM_JSON);
      await store.dispatch("stimulation/addImportedProtocol", parsedStimData);

      const expectedName = store.state.stimulation.protocolList[2].label;
      const expectedLetter = store.state.stimulation.protocolList[2].letter;
      expect(expectedName).toBe(parsedStimData.protocols[0].protocol.name);
      expect(expectedLetter).toBe("B"); // imported letter assignments won't be used, will always be next in line
    });

    test("When a user selects wells with a protocol applied, Then the selected wells should be cleared of any protocol assignments with specified protocol", async () => {
      const testAssigment = {
        0: { letter: "A", color: "#118075", label: "Tester", protocol: { test: null } },
      };

      await store.dispatch("stimulation/handleSelectedWells", testWells.SELECTED);
      await store.commit("stimulation/applySelectedProtocol", testAssigment[0]);
      await store.dispatch("stimulation/handleSelectedWells", testWells.UNSELECTED);
      await store.commit("stimulation/clearSelectedProtocol");

      expect(store.state.stimulation.protocolAssignments).toStrictEqual(testAssigment);
    });

    test("When a user requests to delete the current stimulation by using the trash icon, Then it should reset just the Protocol Viewer and Block View Editor components", async () => {
      await store.commit("stimulation/resetProtocolEditor");
      expect(store.state.stimulation.protocolEditor.subprotocols).toStrictEqual([]);
    });

    test("When a user requests to delete the all of their current changes to entire stim studio, Then it should reset the entire state", async () => {
      store.state.stimulation.protocolAssignments = { test: "test" };
      store.state.stimulation.protocolEditor.subprotocols = ["test", "test1"];

      await store.commit("stimulation/resetState");

      expect(store.state.stimulation.protocolAssignments).toStrictEqual({});
      expect(store.state.stimulation.protocolEditor.subprotocols).toStrictEqual([]);
    });

    test("When a user changes the time unit to seconds, Then it should mutate state to seconds", async () => {
      expect(store.state.stimulation.protocolEditor.timeUnit).toBe("milliseconds");
      await store.commit("stimulation/setTimeUnit", "seconds");
      expect(store.state.stimulation.protocolEditor.timeUnit).toBe("seconds");
    });

    test("When a user wants to zoom in on a the y-axis in the Protocol Viewer, Then the scale will divide by 10", async () => {
      expect(store.state.stimulation.yAxisScale).toBe(120);
      await store.commit("stimulation/setZoomIn", "y-axis");
      expect(store.state.stimulation.yAxisScale).toBe(80);
    });

    test("When a user wants to zoom out on the y-axis, Then the scale will multiple by a power of 10", async () => {
      expect(store.state.stimulation.yAxisScale).toBe(120);
      await store.commit("stimulation/setZoomOut", "y-axis");
      expect(store.state.stimulation.yAxisScale).toBe(180);
    });

    test("When a user makes changes to the protocol order, Then new x and y coordinates will be established and mutated to state", async () => {
      const xValues = [0, 0, 100, 100, 110, 110, 113, 113, 118, 118];
      const yValues = [0, 200, 200, 0, 0, 200, 200, 0, 0, 0];
      const colors = [["b7b7b7", [0, 10]]];

      await store.dispatch("stimulation/handleProtocolOrder", TEST_PROTOCOL_ORDER);
      const { xAxisValues, yAxisValues, repeatColors } = store.state.stimulation;

      expect(xAxisValues).toStrictEqual(xValues);
      expect(yAxisValues).toStrictEqual(yValues);
      expect(repeatColors).toStrictEqual(colors);
    });

    test("When a user wants to save the new protocol by clicking on Save Changes button, Then the new protocol will be committed to state", async () => {
      const { currentAssignment, protocolEditor } = store.state.stimulation;
      currentAssignment.letter = "B";
      currentAssignment.color = "#000000";
      protocolEditor.name = "mockProtocol";

      const expectedProtocol = {
        letter: "B",
        color: "#000000",
        label: "mockProtocol",
        protocol: protocolEditor,
      };

      await store.dispatch("stimulation/addSavedPotocol");
      expect(store.state.stimulation.protocolList[2]).toStrictEqual(expectedProtocol);
    });

    test("When a user wants to save changes to an existing protocol by clicking on Save Changes button, Then the updated protocol will be commited to state in the available protocol list", async () => {
      const { protocolList, protocolEditor, editMode } = store.state.stimulation;

      const selectedProtocol = protocolList[1];
      const { protocol } = protocolList[1];
      const oldName = "Tester";
      const newName = "NewName";

      expect(protocol.name).toBe(oldName);
      await store.dispatch("stimulation/editSelectedProtocol", selectedProtocol);
      expect(protocolEditor.name).toBe(oldName);
      expect(editMode.status).toBe(true);
      await store.commit("stimulation/setProtocolName", newName);
      await store.dispatch("stimulation/addSavedPotocol");

      const test = store.state.stimulation.protocolList[1].protocol.name;
      expect(test).toBe(newName);

      expect(editMode.status).toBe(false);
    });

    test("When a user wants to save changes to an existing protocol by clicking on Save Changes button, Then the edited protocol will be updated in protocol assignments if assigned", async () => {
      const protocolList = store.state.stimulation.protocolList;
      const selectedProtocol = protocolList[1];
      const oldName = "Tester";
      const newName = "NewName";

      await store.dispatch("stimulation/handleSelectedWells", testWells.SELECTED);
      await store.commit("stimulation/applySelectedProtocol", selectedProtocol);

      const previousStatus = store.state.stimulation.stimStatus;
      let protocolAssignments = store.state.stimulation.protocolAssignments;
      const preAssignmentName = protocolAssignments[0].protocol.name;
      expect(preAssignmentName).toBe(oldName);

      await store.dispatch("stimulation/editSelectedProtocol", selectedProtocol);
      await store.commit("stimulation/setProtocolName", newName);
      await store.dispatch("stimulation/addSavedPotocol");

      protocolAssignments = store.state.stimulation.protocolAssignments; // have to get this value again since it is reassigned inside the store
      const postAssignmentName = protocolAssignments[0].protocol.name;
      expect(postAssignmentName).toBe(newName);
      expect(previousStatus).toBe(store.state.stimulation.stimStatus); // shouldn't change if only editing existing assignment
    });

    test("When a user wants to delete an existing protocol by clicking on trash icon, Then the selected protocol will be removed from the list of available protocols, removed from any assigned wells, and the editor will be reset", async () => {
      const protocolList = store.state.stimulation.protocolList;
      const selectedProtocol = protocolList[1];

      await store.dispatch("stimulation/handleSelectedWells", testWells.SELECTED);
      await store.commit("stimulation/applySelectedProtocol", selectedProtocol);
      await store.dispatch("stimulation/editSelectedProtocol", selectedProtocol);
      await store.dispatch("stimulation/handleProtocolEditorReset");

      expect(store.state.stimulation.protocolAssignments).toStrictEqual({});
      expect(protocolList).toHaveLength(1);
    });

    test("When a user adds a repeat delay into the input of the settings panel, Then it will appear at the end of the waveform in the graph", async () => {
      const testDelay = 10;
      const expectedBlock = [[0, 10]];
      await store.dispatch("stimulation/handleNewRestDuration", testDelay);
      const { delayBlocks } = store.state.stimulation;
      expect(delayBlocks).toStrictEqual(expectedBlock);
    });

    test.each([INCOMPATIBLE_PROTOCOL_EXPORT_MULTI, INCOMPATIBLE_PROTOCOL_EXPORT_MULTI.protocols[0].protocol])(
      "When a protocol file is imported, Then the protocol will be converted to latest protocol format if old format is found",
      async (protocols) => {
        await store.dispatch("stimulation/addImportedProtocol", protocols);
        const expectedDetailedPulses = [
          {
            type: "Delay",
            color: "hsla(281, 91%, 41%, 1)",
            pulseSettings: {
              duration: 1000,
              unit: "milliseconds",
            },
            subprotocols: [],
          },
          {
            type: "Monophasic",
            color: "hsla(253, 99%, 58%, 1)",
            pulseSettings: {
              frequency: 10,
              numCycles: 10,
              phaseOneCharge: 100,
              phaseOneDuration: 10,
              postphaseInterval: 90,
              totalActiveDuration: {
                duration: 1000,
                unit: "milliseconds",
              },
            },
            subprotocols: [],
          },
          {
            type: "Biphasic",
            color: "hsla(11, 99%, 55%, 1)",
            pulseSettings: {
              frequency: 1,
              interphaseInterval: 0,
              numCycles: 2,
              phaseOneCharge: 100,
              phaseOneDuration: 10,
              phaseTwoCharge: -100,
              phaseTwoDuration: 10,
              postphaseInterval: 980,
              totalActiveDuration: {
                duration: 2000,
                unit: "milliseconds",
              },
            },
            subprotocols: [],
          },
        ];
        expect(store.state.stimulation.protocolList[2].protocol.detailedSubprotocols).toStrictEqual(
          expectedDetailedPulses
        );
      }
    );
  });
});
