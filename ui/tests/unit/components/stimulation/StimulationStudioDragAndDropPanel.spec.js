import { mount, createLocalVue, shallowMount } from "@vue/test-utils";
import StimulationStudioDragAndDropPanel from "@/components/stimulation/StimulationStudioDragAndDropPanel.vue";
import {
  MONOPHASIC_DROP_ELEMENT,
  BIPHASIC_DROP_ELEMENT,
  TEST_PROTOCOL_LIST_2,
  TEST_PROTOCOL_ORDER_3,
} from "@/tests/sample-stim-protocols/stim-protocols";

import Vuex from "vuex";

const localVue = createLocalVue();
localVue.use(Vuex);
let NuxtStore;
let store;

let wrapper = null;
describe("StimulationStudioDragAndDropPanel.vue", () => {
  beforeAll(async () => {
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
    store.state.stimulation.protocolList = JSON.parse(JSON.stringify(TEST_PROTOCOL_LIST_2));
  });

  afterEach(() => {
    wrapper.destroy();
    jest.clearAllMocks();
  });
  test("When mounting StimulationStudioDragAndDropPanel from the component file, Then there should be no waveforms in the new protocol container", () => {
    wrapper = mount(StimulationStudioDragAndDropPanel, {
      store,
      localVue,
    });
    const protocolList = wrapper.vm.protocolOrder;
    expect(protocolList).toStrictEqual([]);
  });

  test("When a user clicks on trash icons to delete protocol, Then the protocol order in StimulationStudioDragAndDropPanel should empty from the mutation in state", async () => {
    wrapper = mount(StimulationStudioDragAndDropPanel, {
      store,
      localVue,
    });
    wrapper.vm.protocolOrder = ["Biphasic", "Monophasic", "Monophasic"];
    await store.commit("stimulation/resetState");
    expect(wrapper.vm.protocolOrder).toStrictEqual([]);
  });

  test("When a user drops a waveform to the block editor, Then the corresponding modal to should pop up", async () => {
    wrapper = shallowMount(StimulationStudioDragAndDropPanel, {
      store,
      localVue,
    });

    await wrapper.vm.clone({ type: "Monophasic", src: "test" });
    await wrapper.vm.checkType({
      added: {
        element: MONOPHASIC_DROP_ELEMENT,
        newIndex: 4,
      },
    });
    expect(wrapper.vm.modalType).toBe("Monophasic");

    const modalContainer = wrapper.find(".modal-container");
    expect(modalContainer.isVisible()).toBeTruthy();

    await wrapper.vm.onModalClose("Cancel");
    expect(wrapper.vm.modalType).toBeNull();

    await wrapper.vm.clone({ type: "Delay", src: "test" });
    await wrapper.vm.checkType({
      added: {
        element: {
          type: "Delay",
          color: "hsla(45, 100%, 50%, 1)",
          pulseSettings: { duration: "", unit: "milliseconds" },
        },
        newIndex: 4,
      },
    });

    expect(wrapper.vm.selectedPulseSettings).toStrictEqual({ duration: "", unit: "milliseconds" });
    expect(wrapper.vm.openDelayModal).toBe(true);

    const delayContainer = wrapper.find(".delay-container");
    expect(delayContainer.isVisible()).toBeTruthy();

    await wrapper.vm.onModalClose("Cancel");
    expect(wrapper.vm.modalType).toBeNull();
  });

  test("When a user opens a modal to delete waveform, Then when delete is clicked, it will delete", async () => {
    wrapper = mount(StimulationStudioDragAndDropPanel, {
      store,
      localVue,
    });

    await wrapper.setData({ protocolOrder: JSON.parse(JSON.stringify(TEST_PROTOCOL_ORDER_3)) });
    await wrapper.vm.openModalForEdit("Biphasic", 0);
    expect(wrapper.vm.modalType).toBe("Biphasic");
    expect(wrapper.vm.shiftClickImgIdx).toBe(0);
    expect(wrapper.find(".modalOverlay")).toBeTruthy();

    const modalButtons = wrapper.findAll(".span__button-label");
    await modalButtons.at(3).trigger("click");

    expect(wrapper.vm.protocolOrder).toHaveLength(3);
    expect(wrapper.vm.modalType).toBeNull();
  });
  test("When a user selects a protocol to edit, Then the DragAndDropPanel component should get the selected pulse order and unit of time to display for edit", async () => {
    wrapper = mount(StimulationStudioDragAndDropPanel, {
      store,
      localVue,
    });

    const expectedIdx = 0;
    const selectedProtocol = store.state.stimulation.protocolList[1];
    const expectedPulseOrder = store.state.stimulation.protocolList[1].protocol.detailedSubprotocols;
    await store.dispatch("stimulation/editSelectedProtocol", selectedProtocol);

    expect(wrapper.vm.timeUnitsIdx).toBe(expectedIdx);
    expect(wrapper.vm.protocolOrder).toStrictEqual(expectedPulseOrder);
  });

  test("When a user adds a new waveform to the protocol editor and cancels the addition, Then the modal should only appear when it's been cloned and should remove new waveform when cancelled", async () => {
    wrapper = mount(StimulationStudioDragAndDropPanel, {
      store,
      localVue,
    });
    await wrapper.setData({ protocolOrder: JSON.parse(JSON.stringify(TEST_PROTOCOL_ORDER_3)) });
    expect(wrapper.vm.protocolOrder).toHaveLength(4);

    await wrapper.vm.clone({ type: "Biphasic", src: "test" });
    expect(wrapper.vm.cloned).toBe(true);
    await wrapper.vm.checkType({
      added: {
        element: BIPHASIC_DROP_ELEMENT,
        newIndex: 4,
      },
    });

    expect(wrapper.vm.modalType).toBe("Biphasic");

    const cancelButton = wrapper.findAll(".span__button-label").at(1);
    await cancelButton.trigger("click");

    expect(wrapper.vm.protocolOrder).toHaveLength(4);
  });
  test("When changes the order of waveform tiles in scrollable component, Then no modal should appear", async () => {
    wrapper = mount(StimulationStudioDragAndDropPanel, {
      store,
      localVue,
    });
    await wrapper.setData({ protocolOrder: JSON.parse(JSON.stringify(TEST_PROTOCOL_ORDER_3)) });
    expect(wrapper.vm.protocolOrder).toHaveLength(4);

    await wrapper.vm.checkType({
      moved: {
        element: {},
        newIndex: 2,
      },
    });

    expect(wrapper.vm.modalType).toBeNull();
  });

  test("When a user clicks save on the settings for a waveform, Then the setting should save to the corresponding index depending on if it is a new waveform or an edited", async () => {
    const testSettings = "test";
    const testStimSettings = {
      postphaseInterval: "",
      totalActiveDuration: {
        duration: "",
        unit: "milliseconds",
      },
    };
    const wrapper = mount(StimulationStudioDragAndDropPanel, {
      store,
      localVue,
    });
    wrapper.vm.protocolOrder = [
      {
        type: "Biphasic",
        src: "test",
        color: "b7b7b7",
        pulseSettings: {},
      },
    ];
    wrapper.vm.newClonedIdx = 0;
    wrapper.vm.modalType = "Biphasic";

    await wrapper.vm.onModalClose("Save", testSettings, testStimSettings);
    expect(wrapper.vm.protocolOrder[0].pulseSettings).toBe(testSettings);
  });

  test("When a user hovers over a waveform tile, Then the pulse settings will be added to state", async () => {
    wrapper = mount(StimulationStudioDragAndDropPanel, {
      store,
      localVue,
    });

    expect(store.state.stimulation.hoveredPulse).toStrictEqual({
      idx: null,
      indices: [],
      color: null,
    });

    await wrapper.setData({ protocolOrder: JSON.parse(JSON.stringify(TEST_PROTOCOL_ORDER_3)) });
    await store.dispatch("stimulation/handleProtocolOrder", TEST_PROTOCOL_ORDER_3);
    await wrapper.vm.onPulseEnter(1);

    expect(store.state.stimulation.hoveredPulse).toStrictEqual({
      idx: 1,
      indices: [[9, 20]],
      color: "hsla(205, 100%, 50%, 1)",
    });
  });

  test("When a user hovers over a waveform tile, but it's because the user is dragging a tile above, Then the pulse settings not be added", async () => {
    wrapper = mount(StimulationStudioDragAndDropPanel, {
      store,
      localVue,
    });
    const defaultState = {
      idx: null,
      indices: [],
      color: null,
    };
    expect(store.state.stimulation.hoveredPulse).toStrictEqual(defaultState);

    await wrapper.setData({
      protocolOrder: JSON.parse(JSON.stringify(TEST_PROTOCOL_ORDER_3)),
      isDragging: true,
    });
    await store.dispatch("stimulation/handleProtocolOrder", TEST_PROTOCOL_ORDER_3);
    await wrapper.vm.onPulseEnter(1);

    expect(store.state.stimulation.hoveredPulse).toStrictEqual(defaultState);
  });

  test("When a user leaves hover over a waveform tile, Then the pulse settings will be reset", async () => {
    wrapper = mount(StimulationStudioDragAndDropPanel, {
      store,
      localVue,
    });

    await store.dispatch("stimulation/handleProtocolOrder", TEST_PROTOCOL_ORDER_3);
    await wrapper.vm.onPulseEnter(1);
    expect(store.state.stimulation.hoveredPulse).toStrictEqual({
      idx: 1,
      indices: [[9, 20]],
      color: "hsla(205, 100%, 50%, 1)",
    });

    await wrapper.vm.onPulseLeave();
    expect(store.state.stimulation.hoveredPulse).toStrictEqual({
      idx: null,
      indices: [],
      color: null,
    });
  });

  test("When a user selects 'Duplicate' in  waveform modal, Then the current pulse settings will be added into the pulse order right after selected pulse", async () => {
    wrapper = mount(StimulationStudioDragAndDropPanel, {
      store,
      localVue,
    });

    await wrapper.setData({ protocolOrder: JSON.parse(JSON.stringify(TEST_PROTOCOL_ORDER_3)) });
    expect(wrapper.vm.protocolOrder).toHaveLength(4);
    await wrapper.vm.openModalForEdit("Monophasic", 3);

    const duplicateButton = wrapper.findAll(".span__button-label").at(2);
    await duplicateButton.trigger("click");

    expect(wrapper.vm.protocolOrder).toHaveLength(5);
  });

  test("When a selects the Stimulate Until Complete option in the protocol editor, Then the time unit dropdown should become disabled", async () => {
    const testSettings = {
      complete: false,
      stopped: true,
    };
    const wrapper = mount(StimulationStudioDragAndDropPanel, {
      store,
      localVue,
    });

    await store.commit("stimulation/setStopSetting", testSettings.complete);
    expect(wrapper.vm.disableDropdown).toBe(true);
    await store.commit("stimulation/setStopSetting", testSettings.stopped);
    expect(wrapper.vm.disableDropdown).toBe(false);
  });

  test("When a user double clicks a delay block to edit duration, Then the new value should be saved upon close", async () => {
    const wrapper = mount(StimulationStudioDragAndDropPanel, {
      store,
      localVue,
    });

    const idx = 2;

    const delaySettings = {
      duration: 5,
      unit: "seconds",
    };

    await wrapper.setData({ protocolOrder: TEST_PROTOCOL_ORDER_3 });
    await wrapper.vm.openModalForEdit("Delay", idx);
    expect(wrapper.vm.openDelayModal).toBe(true);

    await wrapper.vm.onModalClose("Save", delaySettings);
    expect(wrapper.vm.protocolOrder[idx].pulseSettings.duration).toBe(delaySettings.duration);
  });
});
