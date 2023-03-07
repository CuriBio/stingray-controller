import { mount } from "@vue/test-utils";
import BootstrapVue from "bootstrap-vue";
import StatusWidget from "@/components/status/StatusBar.vue";
import Vue from "vue";
import Vuex from "vuex";
import axios from "axios";
const MockAxiosAdapter = require("axios-mock-adapter");
import { createLocalVue } from "@vue/test-utils";
import { STATUS } from "@/store/modules/flask/enums";
import { STIM_STATUS } from "@/store/modules/stimulation/enums";

let wrapper = null;

const localVue = createLocalVue();
localVue.use(Vuex);
localVue.use(BootstrapVue);

let NuxtStore;
let store;
let mockedAxios;

const textSelector = ".span__status-bar-text";

describe("StatusWidget.vue", () => {
  beforeAll(async () => {
    // note the store will mutate across tests, so make sure to re-create it in beforeEach
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
    mockedAxios = new MockAxiosAdapter(axios);
  });

  afterEach(() => {
    wrapper.destroy();
    mockedAxios.restore();
  });
  describe("systemStatus", () => {
    test("When BE signals corrupt h5 detected, Then show user the error", async () => {
      const propsData = {};
      wrapper = mount(StatusWidget, {
        propsData,
        store,
        localVue,
      });
      const textSelectorH5 = "#h5Warning";
      await store.commit("stimulation/setH5Warning");
      // select the correct button
      Vue.nextTick(() => {
        expect(wrapper.find(textSelectorH5).isVisible()).toBe(true);
        const h5ExitButton = wrapper.findAll(".span__button-label").at(0);
        // check we have the correct button
        expect(h5ExitButton.text()).toBe([]);
        h5ExitButton.trigger("click");
        expect(wrapper.find(textSelectorH5).isVisible()).toBe(false);
      });
    });
    // add test to check that false = not visible
    test.each([
      ["SERVER_BOOTING_UP", "System status: Booting Up..."],
      ["SERVER_STILL_INITIALIZING", "System status: Connecting..."],
      ["SERVER_READY", "System status: Connecting..."],
      ["INITIALIZING_INSTRUMENT", "System status: Initializing..."],
      ["CALIBRATION_NEEDED", "System status: Connected...Calibration Needed"],
      ["CALIBRATING", "System status: Calibrating..."],
      ["CALIBRATED", "System status: Ready"],
      ["BUFFERING", "System status: Preparing for Live View..."],
      ["LIVE_VIEW_ACTIVE", "System status: Live View Active"],
      ["RECORDING", "System status: Recording to File..."],
      ["ERROR", "System status: Error Occurred"],
      ["CHECKING_FOR_UPDATES", "System status: Checking for Firmware Updates..."],
    ])(
      "Given that /shutdown is mocked to return status 200, When Vuex is mutated to the state %s, Then the status text should update to be: %s",
      async (vuexState, expectedText) => {
        const shutdownUrl = "http://localhost:4567/shutdown";
        mockedAxios.onGet(shutdownUrl).reply(200, {});
        const propsData = {};
        wrapper = mount(StatusWidget, {
          propsData,
          store,
          localVue,
        });
        store.commit("flask/setStatusUuid", STATUS[vuexState]);
        await wrapper.vm.$nextTick(); // wait for update

        expect(wrapper.find(textSelector).text()).toBe(expectedText);
      }
    );
    test("When initially mounted, Then the status text matches the Vuex state", async () => {
      const propsData = {};
      store.commit("flask/setStatusUuid", STATUS.CALIBRATING);
      wrapper = mount(StatusWidget, {
        propsData,
        store,
        localVue,
      });
      await wrapper.vm.$nextTick(); // wait for update
      expect(wrapper.find(textSelector).text()).toBe("System status: Calibrating...");
    });

    test.each([
      "InstrumentCreateConnectionError",
      "InstrumentConnectionLostError",
      "InstrumentBadDataError",
      "InstrumentFirmwareError",
    ])(
      "When unique shutdown error gets set to %s in Vuex, Then it will override any status text present before error modal appears",
      async (errorType) => {
        wrapper = mount(StatusWidget, {
          store,
          localVue,
        });
        expect(wrapper.find(textSelector).text()).toBe("System status: Booting Up..."); // initial status
        await store.commit("settings/setShutdownErrorStatus", { errorType });
        expect(wrapper.find(textSelector).text()).toBe(`System status: Error Occurred`);
      }
    );

    test("When unknown error type gets sent through WS, Then the status will still be set to error occurred", async () => {
      const propsData = {};
      wrapper = mount(StatusWidget, {
        propsData,
        store,
        localVue,
      });

      expect(wrapper.find(textSelector).text()).toBe("System status: Booting Up..."); // initial status
      await store.commit("settings/setShutdownErrorStatus", { errorType: "UnknownError" });
      expect(wrapper.find(textSelector).text()).toBe("System status: Error Occurred");
    });

    test("When Vuex is mutated to an unknown UUID, Then the status text should update to include that UUID", async () => {
      const propsData = {};
      wrapper = mount(StatusWidget, {
        propsData,
        store,
        localVue,
      });

      store.commit("flask/setStatusUuid", "3dbb8814-09f1-44db-b7d5-7a9f702beac4");
      await wrapper.vm.$nextTick(); // wait for update
      expect(wrapper.find(textSelector).text()).toBe("System status: 3dbb8814-09f1-44db-b7d5-7a9f702beac4");
    });
    test("Given that the http response is 404 for api request /shutdown, When Vuex is mutated to an ERROR UUID, Then the status text should update as 'Error Occurred' and the the dialog of ErrorCatchWidget is visible", async () => {
      const shutdownUrl = "http://localhost:4567/shutdown";
      mockedAxios.onGet(shutdownUrl).reply(404);
      const propsData = {};
      wrapper = mount(StatusWidget, {
        propsData,
        store,
        localVue,
        attachToDocument: true,
      });

      expect(wrapper.contains("#error-catch")).toBe(true);
      const modal = wrapper.find("#error-catch");
      expect(modal.isVisible()).toBe(false);
      store.commit("flask/setStatusUuid", STATUS.ERROR);
      await wrapper.vm.$nextTick(); // wait for update
      expect(wrapper.find(textSelector).text()).toBe("System status: Error Occurred");
      Vue.nextTick(() => {
        expect(modal.isVisible()).toBe(true);
      });
    });
    test("When Vuex is mutated to an ERROR UUID and shutdown status was set to known error, Then the status text should not update to 'Error Occurred'", async () => {
      const propsData = {};
      wrapper = mount(StatusWidget, {
        propsData,
        store,
        localVue,
        attachToDocument: true,
      });

      await store.commit("settings/setShutdownErrorStatus", {
        errorType: "InstrumentCreateConnectionError",
      });
      store.commit("flask/setStatusUuid", STATUS.ERROR);
      expect(wrapper.find(textSelector).text()).toBe(`System status: Error Occurred`);
    });
    test("When Vuex is mutated to an UPDATE ERROR UUID, Then the status text should update as 'Error During Firmware Update' and the the dialog of ErrorCatchWidget is visible", async () => {
      const propsData = {};
      wrapper = mount(StatusWidget, {
        propsData,
        store,
        localVue,
        attachToDocument: true,
      });

      expect(wrapper.contains("#error-catch")).toBe(true);
      const modal = wrapper.find("#error-catch");

      store.commit("flask/setStatusUuid", STATUS.UPDATE_ERROR);
      await wrapper.vm.$nextTick(); // wait for update
      expect(wrapper.find(textSelector).text()).toBe("System status: Error During Firmware Update");
      Vue.nextTick(() => {
        expect(modal.isVisible()).toBe(true);
      });

      wrapper.vm.closeModalsById(["error-catch"]); // the event of ok-clicked got invoked.

      Vue.nextTick(() => {
        expect(modal.isVisible()).toBe(false);
      });
    });
    test.each([
      "SERVER_BOOTING_UP",
      "SERVER_STILL_INITIALIZING",
      "SERVER_READY",
      "INITIALIZING_INSTRUMENT",
      "CALIBRATION_NEEDED",
      "CALIBRATING",
      "CALIBRATED",
      "UPDATES_NEEDED",
      "UPDATES_COMPLETE",
      "UPDATE_ERROR",
      "ERROR",
    ])(
      "When a user wants to exit the desktop app, Then the closure warning modals should not appear if there are no active processes or fw update",
      async (vuexState) => {
        const confirmationSpy = jest.spyOn(StatusWidget.methods, "handleConfirmation");
        wrapper = mount(StatusWidget, {
          store,
          localVue,
        });

        await store.commit("flask/setStatusUuid", STATUS[vuexState]);
        await store.commit("settings/setConfirmationRequest", true);
        expect(confirmationSpy).toHaveBeenCalledWith(1);

        Vue.nextTick(() => {
          expect(wrapper.find("#fw-closure-warning").isVisible()).toBe(false);
          expect(wrapper.find("#ops-closure-warning").isVisible()).toBe(false);
        });
      }
    );

    test.each(["BUFFERING", "LIVE_VIEW_ACTIVE", "RECORDING", "CALIBRATING"])(
      "When a user wants to exit the desktop app, Then the closure warning modal should appear if there are active processes",
      async (vuexState) => {
        wrapper = mount(StatusWidget, {
          store,
          localVue,
        });
        await store.commit("flask/setStatusUuid", STATUS[vuexState]);

        await store.commit("settings/setConfirmationRequest", false);
        Vue.nextTick(() => {
          expect(wrapper.find("#ops-closure-warning").isVisible()).toBe(false);
        });

        await store.commit("settings/setConfirmationRequest", true);
        Vue.nextTick(() => {
          expect(wrapper.find("#ops-closure-warning").isVisible()).toBe(true);
        });
      }
    );

    test("When a user wants to exit the desktop app and a stimulation is active, Then the closure warning modal should appear", async () => {
      wrapper = mount(StatusWidget, {
        store,
        localVue,
      });

      await store.commit("stimulation/setStimPlayState", true);
      await store.commit("settings/setConfirmationRequest", false);
      Vue.nextTick(() => {
        expect(wrapper.find("#ops-closure-warning").isVisible()).toBe(false);
      });

      await store.commit("settings/setConfirmationRequest", true);
      Vue.nextTick(() => {
        expect(wrapper.find("#ops-closure-warning").isVisible()).toBe(true);
      });
    });

    test.each(["DOWNLOADING_UPDATES", "INSTALLING_UPDATES"])(
      "When a user wants to exit the desktop app, Then the fw closure warning modal should appear if a fw update is in progress",
      async (vuexState) => {
        wrapper = mount(StatusWidget, {
          store,
          localVue,
        });
        await store.commit("flask/setStatusUuid", STATUS[vuexState]);

        await store.commit("settings/setConfirmationRequest", false);
        Vue.nextTick(() => {
          expect(wrapper.find("#fw-closure-warning").isVisible()).toBe(false);
        });

        await store.commit("settings/setConfirmationRequest", true);
        Vue.nextTick(() => {
          expect(wrapper.find("#fw-closure-warning").isVisible()).toBe(true);
        });
      }
    );

    test.each([
      ["SERVER_BOOTING_UP", "initializing"],
      ["SERVER_STILL_INITIALIZING", "initializing"],
      ["SERVER_READY", "initializing"],
      ["INITIALIZING_INSTRUMENT", "initializing"],
      ["CALIBRATING", "initializing"],
      ["CHECKING_FOR_UPDATES", "initializing"],
      ["DOWNLOADING_UPDATES", "initializing"],
      ["INSTALLING_UPDATES", "initializing"],
      ["UPDATES_NEEDED", "initializing"],
      ["UPDATES_COMPLETE", "initializing"],
      ["UPDATE_ERROR", "initializing"],
      ["LIVE_VIEW_ACTIVE", "active-processes"],
      ["RECORDING", "active-processes"],
      ["BUFFERING", "active-processes"],
    ])(
      "When the desktop app is in state %s and the daCheck prop changes to true, Then the %s modal will appear that data analysis cannot be performed at this time",
      async (systemStatus, modal) => {
        wrapper = mount(StatusWidget, {
          store,
          localVue,
        });
        await store.commit("flask/setStatusUuid", STATUS[systemStatus]);
        await wrapper.setProps({ daCheck: true });

        Vue.nextTick(() => {
          expect(wrapper.find(`#${modal}-warning`).isVisible()).toBe(true);
        });
      }
    );
    test.each(["CALIBRATION_NEEDED", "CALIBRATED"])(
      "When the desktop app is in state %s and the daCheck prop changes to true, Then closeDaCheckModal event will be emitted with 1",
      async (systemStatus) => {
        wrapper = mount(StatusWidget, {
          store,
          localVue,
        });
        await store.commit("flask/setStatusUuid", STATUS[systemStatus]);
        await wrapper.setProps({ daCheck: true });

        expect(wrapper.emitted("closeDaCheckModal")).toStrictEqual([[1]]);

        // assert no second call gets made
        await wrapper.setProps({ daCheck: false });
        expect(wrapper.emitted("closeDaCheckModal")).toStrictEqual([[1]]);
      }
    );

    test("When user closes warning that processes are active by selecting button at index 1 'Continue' and both stim and playback states are active, Then both actions will be dispatched to stop all corresponding processes", async () => {
      wrapper = mount(StatusWidget, {
        store,
        localVue,
      });
      const actionSpy = jest.spyOn(store, "dispatch").mockImplementation(() => null);
      await store.commit("flask/setStatusUuid", STATUS.RECORDING);
      await store.commit("stimulation/setStimPlayState", true);
      await wrapper.vm.closeDaCheckModal(1);

      expect(actionSpy).toHaveBeenCalledWith("stimulation/stopStimulation");
      expect(actionSpy).toHaveBeenCalledWith("playback/stopActiveProcesses");
      expect(wrapper.emitted("closeDaCheckModal")).toStrictEqual([[1]]);
    });

    test.each([
      ["stimulation/setStimPlayState", true, "stimulation/stopStimulation", "playback/stopActiveProcesses"],
      [
        "flask/setStatusUuid",
        STATUS.RECORDING,
        "playback/stopActiveProcesses",
        "stimulation/stopStimulation",
      ],
    ])(
      "When user closes warning that processes are active by selecting button at index 1 'Continue', Then one action will be dispatched to stop all corresponding processes",
      async (initialAction, state, expectedCall, notExpectedCall) => {
        wrapper = mount(StatusWidget, {
          store,
          localVue,
        });
        const actionSpy = jest.spyOn(store, "dispatch").mockImplementation(() => null);
        await store.commit(initialAction, state);
        await wrapper.vm.closeDaCheckModal(1);

        expect(actionSpy).toHaveBeenCalledWith(expectedCall);
        expect(actionSpy).not.toHaveBeenCalledWith(notExpectedCall);
        expect(wrapper.emitted("closeDaCheckModal")).toStrictEqual([[1]]);
      }
    );

    test("When user closes warning that processes are active by selecting button at index 0 'Cancel', Then actions will not be called to stop active processes", async () => {
      wrapper = mount(StatusWidget, {
        store,
        localVue,
      });
      const actionSpy = jest.spyOn(store, "dispatch").mockImplementation(() => null);
      await store.commit("flask/setStatusUuid", STATUS.RECORDING);
      await store.commit("stimulation/setStimPlayState", true);
      await wrapper.vm.closeDaCheckModal(0);

      expect(actionSpy).not.toHaveBeenCalledWith("stimulation/stopStimulation");
      expect(actionSpy).not.toHaveBeenCalledWith("playback/stopActiveProcesses");
      expect(wrapper.emitted("closeDaCheckModal")).toStrictEqual([[0]]);
    });
  });
  describe("stimStatus", () => {
    test.each([
      ["CALIBRATION_NEEDED", "Stim status: Calibration Needed", { 1: {} }],
      ["NO_PROTOCOLS_ASSIGNED", "Stim status: No protocols have been assigned", {}],
      ["CONFIG_CHECK_NEEDED", "Stim status: Configuration Check Needed", { 1: {} }],
      ["CONFIG_CHECK_IN_PROGRESS", "Stim status: Configuration Check in Progress...", { 1: {} }],
      ["CONFIG_CHECK_COMPLETE", "Stim status: Configuration Check Complete", { 1: {} }],
      ["READY", "Stim status: Ready", { 1: {} }],
      ["STIM_ACTIVE", "Stim status: Stimulating...", { 1: {} }],
      ["SHORT_CIRCUIT_ERROR", "Stim status: Short Circuit Error", {}],
      ["ERROR", "Stim status: Error Occurred", {}],
    ])(
      "When stim'sstimStatus gets mutated to %s, Then the status text should update to be: %s",
      async (vuexState, expectedText, assignments) => {
        const propsData = { stimSpecific: true };
        wrapper = mount(StatusWidget, {
          propsData,
          store,
          localVue,
        });

        store.state.stimulation.protocolAssignments = assignments;

        await store.commit("stimulation/setStimStatus", stimStatus[vuexState]);
        expect(wrapper.find(textSelector).text()).toBe(expectedText);
      }
    );
    test("When initially mounted, Then the stim status text matches the Vuex state", async () => {
      const propsData = { stimSpecific: true };
      await store.commit("stimulation/setStimStatus", STIM_STATUS.CONFIG_CHECK_NEEDED);

      wrapper = mount(StatusWidget, {
        propsData,
        store,
        localVue,
      });
      expect(wrapper.find(textSelector).text()).toBe("Stim status: No protocols have been assigned");
    });
  });
});
