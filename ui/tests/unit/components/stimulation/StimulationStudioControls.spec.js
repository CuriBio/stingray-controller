import Vuex from "vuex";
import { createLocalVue, mount } from "@vue/test-utils";
import StimulationStudioControls from "@/components/stimulation/StimulationStudioControls.vue";
import { STIM_STATUS } from "@/store/modules/stimulation/enums";

describe("store/stimulation", () => {
  const localVue = createLocalVue();
  localVue.use(Vuex);
  let NuxtStore;
  let store;

  beforeAll(async () => {
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test("When StimulationStudioControls mounts, Then the initial play state should be false", () => {
    const wrapper = mount(StimulationStudioControls, {
      store,
      localVue,
    });

    expect(wrapper.vm.playState).toBe(false);
  });

  test("Given a stimulation is active, When a user clicks the button to turn off stimulation, Then a signal should be dispatched to BE", async () => {
    const dispatchSpy = jest.spyOn(store, "dispatch");
    dispatchSpy.mockImplementation(async () => await store.commit("stimulation/setStimPlayState", false));

    store.state.stimulation.protocolAssignments = { test: "assignment" };

    const wrapper = mount(StimulationStudioControls, {
      store,
      localVue,
    });

    await store.commit("stimulation/setStimStatus", STIM_STATUS.STIM_ACTIVE);
    wrapper.vm.playState = true;
    // direct call to bypass bootstrap component, jest can't find bootstrap elements
    const testEvent = { preventDefault: jest.fn() };
    await wrapper.vm.handlePlayStop(testEvent);

    expect(dispatchSpy).toHaveBeenCalledWith("stimulation/stopStimulation");
  });

  test("Given there are no wells assigned with a protocol, When a user clicks to start a stimulation, Then no signal should be dispatched to BE", async () => {
    const wrapper = mount(StimulationStudioControls, {
      store,
      localVue,
    });

    // direct call to bypass bootstrap component, jest can't find bootstrap elements
    const testEvent = { preventDefault: jest.fn() };
    await wrapper.vm.handlePlayStop(testEvent);

    expect(wrapper.vm.playState).toBe(false);
  });

  test("Given a stimulation is inactive and there are protocol assigned wells, When a user clicks the button to turn on stimulation, Then a signal should be dispatched to BE", async () => {
    const dispatchSpy = jest.spyOn(store, "dispatch");
    dispatchSpy.mockImplementation(async () => await store.commit("stimulation/setStimPlayState", true));

    store.state.stimulation.protocolAssignments = {
      test: "assignment",
    };
    await store.commit("stimulation/setStimStatus", STIM_STATUS.READY);
    const wrapper = mount(StimulationStudioControls, {
      store,
      localVue,
      attachToDocument: true,
    });

    // direct call to bypass bootstrap component, jest can't find bootstrap elements
    const testEvent = {
      preventDefault: jest.fn(),
    };

    await wrapper.vm.handlePlayStop(testEvent);

    // trigger document event listener to close modal
    await wrapper.trigger("click");

    expect(wrapper.vm.playState).toBe(true);
    expect(dispatchSpy).toHaveBeenCalledWith("stimulation/createProtocolMessage");
  });

  test("When setStimPlayState is called with different values, Then current gradient is updated correctly", async () => {
    const wrapper = mount(StimulationStudioControls, {
      store,
      localVue,
    });

    store.commit("stimulation/setStimPlayState", true);
    await wrapper.vm.$nextTick(); // wait for update
    expect(wrapper.vm.currentGradient).toStrictEqual(wrapper.vm.activeGradient);
    store.commit("stimulation/setStimPlayState", false);
    await wrapper.vm.$nextTick(); // wait for update
    expect(wrapper.vm.currentGradient).toStrictEqual(wrapper.vm.inactiveGradient);
  });

  test.each([
    ["ERROR", "Cannot start a stimulation with error"],
    ["SHORT_CIRCUIT_ERROR", "Cannot start a stimulation with error"],
    ["CONFIG_CHECK_NEEDED", "Configuration check needed"],
    ["CONFIG_CHECK_IN_PROGRESS", "Configuration check needed"],
  ])(
    "When Vuex's stimStatus changes state to %s and protocols are assigned to wells, Then the stim start tooltip will have an updated message %s",
    async (status, expectedMessage) => {
      const wrapper = mount(StimulationStudioControls, {
        store,
        localVue,
      });

      await store.commit("system/setBarcode", {
        type: "stimBarcode",
        newValue: "MS2022001000",
        isValid: true,
      });

      store.state.stimulation.protocolAssignments = { 1: {} };

      await store.commit("stimulation/setStimPlayState", false);
      await store.commit("stimulation/setStimStatus", STIM_STATUS[status]);

      expect(wrapper.find("#start-popover-msg").text()).toBe(expectedMessage);
      expect(wrapper.vm.playState).toBe(false);
    }
  );

  test.each([
    ["ERROR", "Cannot start a stimulation with error"],
    ["SHORT_CIRCUIT_ERROR", "Cannot start a stimulation with error"],
    ["CONFIG_CHECK_NEEDED", "No protocols have been assigned"],
    ["NO_PROTOCOLS_ASSIGNED", "No protocols have been assigned"],
  ])(
    "When Vuex's stimStatus changes state to %s and no protocols have been assigned, Then the stim start tooltip will have an updated message %s",
    async (status, expectedMessage) => {
      const wrapper = mount(StimulationStudioControls, {
        store,
        localVue,
      });

      await store.commit("system/setBarcode", {
        type: "stimBarcode",
        newValue: "MS2022001000",
        isValid: true,
      });

      await store.commit("stimulation/setStimPlayState", false);
      await store.commit("stimulation/setStimStatus", STIM_STATUS[status]);

      expect(wrapper.find("#start-popover-msg").text()).toBe(expectedMessage);
      expect(wrapper.vm.playState).toBe(false);
    }
  );

  test.each([
    ["MS2022001000", true, "No protocols have been assigned"],
    ["invalidBarcode", false, "Must have a valid Stimulation Lid Barcode"],
  ])(
    "When Vuex's stimStatus changes state to ready and stim barcodes value is changed to %s and validity is %s , Then the stim start tooltip will have an updated message %s",
    async (newValue, isValid, message) => {
      const wrapper = mount(StimulationStudioControls, {
        store,
        localVue,
      });
      await store.commit("stimulation/setStimPlayState", false);
      await store.commit("stimulation/setStimStatus", STIM_STATUS.READY);
      await store.commit("system/setBarcode", {
        type: "stimBarcode",
        newValue,
        isValid,
      });

      expect(wrapper.find("#start-popover-msg").text()).toBe(message);
    }
  );

  test.each([
    [true, "STIM_ACTIVE", 0],
    [false, "CONFIG_CHECK_NEEDED", 1],
  ])(
    "When stim play state is %s and user clicks on the configuration check icon to start, Then it will only get called when stimulation is inactive",
    async (playState, stimStatus, calls) => {
      const actionSpy = jest.spyOn(store, "dispatch").mockImplementation(() => {});
      const wrapper = mount(StimulationStudioControls, {
        store,
        localVue,
      });
      store.state.stimulation.protocolAssignments = {
        4: {},
      };
      await store.commit("stimulation/setStimStatus", STIM_STATUS[stimStatus]);
      await store.commit("stimulation/setStimPlayState", playState);
      await store.commit("system/setBarcode", {
        type: "stimBarcode",
        newValue: "MS2022001000",
        isValid: true,
      });

      await wrapper.find(".svg__config-check-container").trigger("click");
      expect(actionSpy).toHaveBeenCalledTimes(calls);
    }
  );
});
