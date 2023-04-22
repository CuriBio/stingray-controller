import { mount, createLocalVue } from "@vue/test-utils";
import StimulationStudioBlockViewEditor from "@/components/stimulation/StimulationStudioBlockViewEditor.vue";
import Vuex from "vuex";
import { TEST_PROTOCOL_LIST_2 } from "@/tests/sample-stim-protocols/stim-protocols";

const localVue = createLocalVue();
localVue.use(Vuex);
let NuxtStore;
let store;

describe("StimulationStudioDragAndDropPanel.vue", () => {
  beforeAll(async () => {
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
    store.state.stimulation.protocolList = JSON.parse(JSON.stringify(TEST_PROTOCOL_LIST_2));
  });

  test("When mounting StimulationStudioDragAndDropPanel from the component file, Then default tab displayed should be basic, but can toggle with clicking each tab", async () => {
    const wrapper = mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });
    expect(wrapper.vm.activeTab).toBe("Basic");
    await wrapper.find("#Advanced").trigger("click");
    expect(wrapper.vm.activeTab).toBe("Advanced");
    await wrapper.find("#Basic").trigger("click");
    expect(wrapper.vm.activeTab).toBe("Basic");
  });

  test("When a user wants to open a protocol settings to edit, Then the mutation will trigger saved settings to appear in the protocol editor", async () => {
    const wrapper = mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });
    const testParam1 = store.state.stimulation.protocolList[1];
    const testParam2 = {
      // for testing and building other fxns
      letter: "B",
      color: "#118075",
      label: "mockTester",
      protocol: {
        name: "mockTester",
        stimulationType: "C",
        runUntilStopped: true,
        restDuration: 40,
        timeUnit: "milliseconds",
        subprotocols: [],
        detailedSubprotocols: [],
      },
    };

    await store.dispatch("stimulation/editSelectedProtocol", testParam1);
    expect(wrapper.vm.currentLetter).toBe(testParam1.letter);
    expect(wrapper.vm.restDuration).toBe("20");
    expect(wrapper.vm.stopOptionIdx).toBe(1);
    expect(wrapper.vm.disabledTime).toBe(true);

    await store.dispatch("stimulation/editSelectedProtocol", testParam2);
    expect(wrapper.vm.currentLetter).toBe(testParam2.letter);
    expect(wrapper.vm.restDuration).toBe("40");
    expect(wrapper.vm.stopOptionIdx).toBe(0);
    expect(wrapper.vm.disabledTime).toBe(false);
  });

  test("When a user adds input to frequency input, Then the change will be recorded in data", async () => {
    const wrapper = mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });

    await wrapper.find("#input-widget-field-protocol-rest").setValue("5");
    expect(wrapper.vm.restDuration).toBe("5");
  });

  test("When a user adds new protocol name, Then it will be checked if it is a unique name or if it already exists", async () => {
    const wrapper = mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });
    await wrapper.vm.checkNameValidity("test");
    expect(wrapper.vm.nameValidity).toBe("border: 1px solid #19ac8a");
    expect(wrapper.vm.errorMessage).toBe("");

    await wrapper.vm.checkNameValidity("");
    expect(wrapper.vm.nameValidity).toBe("");
    expect(wrapper.vm.errorMessage).toBe("");

    await wrapper.vm.checkNameValidity("Tester");
    expect(wrapper.vm.nameValidity).toBe("border: 1px solid #bd3532");
    expect(wrapper.vm.errorMessage).toBe("*Protocol name already exists");
  });

  test("When a user selects from the stimulation type dropdown, Then the corresponding selection is stored", async () => {
    const wrapper = mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });
    await wrapper.findAll("li").at(1).trigger("click");
    expect(store.state.stimulation.protocolEditor.stimulationType).toBe("C");
  });

  test("When a user imports a new protocol, Then the the next available protocol letter/color assignment will get updated", async () => {
    const updateSpy = jest.spyOn(StimulationStudioBlockViewEditor.methods, "updateProtocols");
    mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });
    const testProtocol = { label: "test", color: "#123456", letter: "B" };
    await store.commit("stimulation/setNewProtocol", testProtocol);
    expect(updateSpy).toHaveBeenCalledWith();
  });

  test("When a user clicks the Clear All button, Then the dropdowns will reset to default value", async () => {
    const wrapper = mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });

    await wrapper.setData({
      protocolName: "testName",
      restDuration: "10",
      nameValidity: "border: 1px solid #19ac8a",
    });

    await store.commit("stimulation/resetState");

    expect(wrapper.vm.protocolName).toBe("");
    expect(wrapper.vm.restDuration).toBe("0");
    expect(wrapper.vm.nameValidity).toBe("");
  });

  test("When 'Stimulate Until Complete' is selected, Then the input and time unit dropdown will be disabled", async () => {
    const wrapper = mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });
    const toggleStopOptions = wrapper.find("#smallDropdown_stopOptions");
    const visibleOption = wrapper.find("#stopOptions_1");

    expect(wrapper.vm.disabledTime).toBe(false);

    await toggleStopOptions.trigger("click");
    await visibleOption.trigger("click");

    expect(wrapper.vm.disabledTime).toBe(true);
  });

  test("When a user clicks the trash icon and deletes the protocol, Then it should reset local data and mutate state", async () => {
    const wrapper = mount(StimulationStudioBlockViewEditor, {
      store,
      localVue,
    });
    await wrapper.find("#trashIcon").trigger("click");
    expect(wrapper.find("#del-protocol").isVisible()).toBe(true);
    await wrapper.vm.closeDeleteProtocolModal();
    expect(wrapper.find("#del-protocol").isVisible()).toBe(false);
  });
});
