import { mount, createLocalVue } from "@vue/test-utils";
import StimulationStudioCreateAndEdit from "@/components/stimulation/StimulationStudioCreateAndEdit.vue";
import SelectDropDown from "@/components/basic-widgets/SelectDropDown.vue";
import { TEST_PROTOCOL_LIST_2 } from "@/tests/sample-stim-protocols/stim-protocols";

import Vuex from "vuex";

const localVue = createLocalVue();
localVue.use(Vuex);
let NuxtStore;
let store;

describe("StimulationStudioCreateAndEdit.vue", () => {
  beforeAll(async () => {
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
    store.state.stimulation.protocolList = JSON.parse(JSON.stringify(TEST_PROTOCOL_LIST_2));
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test("When mounting StimulationStudioCreateAndEdit from the component file, Then the correct number of protocols from state should appear in the drop down selection", () => {
    const wrapper = mount(StimulationStudioCreateAndEdit, {
      store,
      localVue,
    });
    const labeledProtocols = store.state.stimulation.protocolList.length - 1;
    const targetSpan = wrapper.findAll("li");
    expect(targetSpan).toHaveLength(labeledProtocols);
  });

  test("When a user clicks on apply selection, Then selected protocol should be applied to all wells in selected wells state and added to protocol assignments", async () => {
    const wrapper = mount(StimulationStudioCreateAndEdit, {
      store,
      localVue,
    });
    await store.dispatch("stimulation/handleSelectedWells", [false, true, false, true]);
    const options = wrapper.findAll("li");
    await options.at(0).trigger("click");
    await wrapper.vm.handleClick(0);
    const expectedValue = store.state.stimulation.protocolList[wrapper.vm.selectedProtocolIdx];
    store.state.stimulation.selectedWells.map((well) => {
      expect(store.state.stimulation.protocolAssignments[well]).toBe(expectedValue);
    });
  });

  test("When a user clicks on clear selection, Then selected protocol should be removed from protocol assignments", async () => {
    const wrapper = mount(StimulationStudioCreateAndEdit, {
      store,
      localVue,
    });
    await store.dispatch("stimulation/handleSelectedWells", [false, true, false, true]);
    const options = wrapper.findAll("li");
    await options.at(0).trigger("click");
    await wrapper.vm.handleClick(0);

    expect(store.state.stimulation.protocolAssignments[1]).toBeTruthy();

    await store.dispatch("stimulation/handleSelectedWells", [false, true, false, false]);
    await wrapper.vm.handleClick(1);
    expect(store.state.stimulation.protocolAssignments[1]).toBeFalsy();
  });

  test("When the dropdown is rendered to the page in the StimulationStudioCreateAndEdit component, Then there should be no title", () => {
    mount(SelectDropDown, {
      localVue,
      store,
      propsData: {
        optionsText: ["test"],
      },
    });

    const inputHeightBackground = SelectDropDown.computed.inputHeightBackground.call({
      titleLabel: "",
    });
    const inputWidgetTop = SelectDropDown.computed.inputWidgetTop.call({
      titleLabel: "",
    });
    expect(inputHeightBackground).toBe(60);
    expect(inputWidgetTop).toBe(0);
  });

  test("When a user selects Create New in the protocol dropdown, Then the protocol editor will reset to be empty", async () => {
    const resetSpy = jest.spyOn(StimulationStudioCreateAndEdit.methods, "resetProtocolEditor");
    const editSpy = jest.spyOn(StimulationStudioCreateAndEdit.methods, "editSelectedProtocol");

    const wrapper = mount(StimulationStudioCreateAndEdit, {
      store,
      localVue,
    });

    await wrapper.findAll("li").at(0).trigger("click");

    expect(editSpy).toHaveBeenCalledTimes(1);

    await wrapper.findAll("li").at(0).trigger("click");

    expect(resetSpy).toHaveBeenCalledTimes(1);
  });

  test("When a user selects Use Active Stim Settings button to edit a selected protocol, Then the protocol will be dispatched to fill the protocol editor and sent to parent component", async () => {
    const actionSpy = jest.spyOn(store, "dispatch");
    const wrapper = mount(StimulationStudioCreateAndEdit, {
      store,
      localVue,
    });
    await wrapper.findAll("li").at(0).trigger("click");

    expect(actionSpy).toHaveBeenCalledTimes(1);
  });

  test("When clicks on export protocol button, Then action will be dispatched to store", async () => {
    const exportSpy = jest.spyOn(StimulationStudioCreateAndEdit.methods, "handleExport");
    window.webkitURL.createObjectURL = function () {};

    const wrapper = mount(StimulationStudioCreateAndEdit, {
      store,
      localVue,
    });
    await wrapper.vm.handleImportExport(1);
    await wrapper.vm.handleImportExport(0);

    expect(exportSpy).toHaveBeenCalledTimes(1);
  });

  test("When clicks on import protocol button, Then action will be dispatched to store", async () => {
    const importSpy = jest
      .spyOn(FileReader.prototype, "readAsText")
      .mockImplementation(() => "test successful");
    const wrapper = mount(StimulationStudioCreateAndEdit, {
      store,
      localVue,
      attachToDocument: true,
    });

    await wrapper.findAll("#import_export_button").at(0).trigger("click");
    // calling directly here because input element gets removed before it can be manually clicked here on the wrapper
    wrapper.vm.handleImport([new File([new Blob()], "testFilename")]);
    expect(importSpy).toHaveBeenCalledTimes(1);
  });

  test("When a user clicks on Clear All to reset new protocol, Then the dropdown should reset to default option", async () => {
    const wrapper = mount(StimulationStudioCreateAndEdit, {
      store,
      localVue,
    });
    await store.commit("stimulation/resetState");
    expect(wrapper.vm.selectedProtocolIdx).toBe(0);
  });

  test("When a user imports a new protocol, Then the dropdown will default to 0 and the list length will increase accordingly", async () => {
    const mockProtocol = {
      label: "test",
      protocol: {
        stimulationType: "C",
        detailedSubprotocols: [],
        subprotocols: [],
      },
    };
    const wrapper = mount(StimulationStudioCreateAndEdit, {
      store,
      localVue,
    });
    expect(store.state.stimulation.protocolList).toHaveLength(2);

    await store.commit("stimulation/setNewProtocol", mockProtocol);

    expect(wrapper.vm.selectedProtocolIdx).toBe(0);
    expect(store.state.stimulation.protocolList).toHaveLength(3);
  });
});
