import Vuex from "vuex";
import { createLocalVue } from "@vue/test-utils";
import { STIM_STATUS } from "@/store/modules/stimulation/enums";
import { socket as socketClientSide } from "@/store/plugins/websocket";
import { ERRORS } from "../../../store/modules/settings/enums.js";

const validPlateBarcodeOld = "ML2022001000";
const validPlateBarcodeBeta1 = "ML22001000-1";
const validPlateBarcodeBeta2 = "ML22001000-2";
const validStimBarcodeOld = "MS2022001000";

const http = require("http");
const ioServer = require("socket.io");

describe("store/system", () => {
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

  describe("system/mutations", () => {
    test.each([true, false])(
      "When setFirmwareUpdateAvailable is commited, Then firmwareUpdateDurMins is updated accordingly",
      (channel) => {
        const updateInfo = { channelFwUpdate: channel };
        store.commit("system/setFirmwareUpdateAvailable", updateInfo);
        expect(store.state.system.firmwareUpdateDurMins).toStrictEqual(channel ? 5 : 1);
      }
    );
    test.each([true, false])(
      "When setFirmwareUpdateAvailable is commited, Then firmwareUpdateAvailable is updated accordingly",
      (update) => {
        const updateInfo = { firmwareUpdateAvailable: update };
        store.commit("system/setFirmwareUpdateAvailable", updateInfo);
        expect(store.state.system.firmwareUpdateAvailable).toStrictEqual(update);
      }
    );
  });
  describe("websocket", () => {
    let httpServer;
    let wsServer;
    let socketServerSide;

    beforeAll((done) => {
      httpServer = http.createServer().listen(4567); // TODO use constant here
      wsServer = ioServer(httpServer);
      // wait for connection
      wsServer.on("connect", (socket) => {
        socketServerSide = socket;
        done();
      });
    });

    afterEach(() => {
      // event handlers persist through tests, so clear them all after each test
      socketClientSide.off();
    });

    afterAll(() => {
      if (socketServerSide.connected) {
        socketServerSide.disconnect();
      }
      wsServer.close();
      httpServer.close();
    });

    test("Given ws client has a 'message' event handler, When ws server emits a 'message' event, Then client receives message", async () => {
      // Sanity test for websockets
      const expectedMessage = "Test Message";

      await new Promise((resolve) => {
        socketClientSide.on("message", (message) => {
          expect(message).toBe(expectedMessage);
          resolve();
        });
        socketServerSide.send(expectedMessage);
      });
    });

    test("When backend emits stimulatorCircuitStatus message with short circuit errors, Then ws client updates stim status to short circuit error", async () => {
      // confirm precondition
      const initialStatuses = store.state.stimulation.stimulatorCircuitStatuses;
      expect(initialStatuses).toHaveLength(0);

      const stimulatorStatuses = new Array(24)
        .fill("open", 0, 10)
        .fill("media", 10, 20)
        .fill("short", 20, 24);

      const stimulatorStatusesObj = {};
      stimulatorStatuses.map((status, wellIdx) => {
        stimulatorStatusesObj[`${wellIdx}`] = status;
      });

      await new Promise((resolve) => {
        socketServerSide.emit("stimulator_circuit_statuses", JSON.stringify(stimulatorStatusesObj), (ack) => {
          resolve(ack);
        });
      });

      const updatedStatuses = store.state.stimulation.stimulatorCircuitStatuses;
      const stimStatus = store.state.stimulation.stimStatus;

      expect(updatedStatuses).toStrictEqual(initialStatuses);
      expect(stimStatus).toBe(STIM_STATUS.SHORT_CIRCUIT_ERROR);
    });

    test("When backend emits stimulatorCircuitStatus message with error status, Then ws client updates stim status to short circuit error", async () => {
      // confirm precondition
      const initialStatuses = store.state.stimulation.stimulatorCircuitStatuses;
      expect(initialStatuses).toHaveLength(0);

      const stimulatorStatuses = new Array(24)
        .fill("open", 0, 10)
        .fill("media", 10, 20)
        .fill("error", 20, 24);

      await new Promise((resolve) => {
        socketServerSide.emit("stimulator_circuit_statuses", JSON.stringify(stimulatorStatuses), (ack) => {
          resolve(ack);
        });
      });

      const updatedStatuses = store.state.stimulation.stimulatorCircuitStatuses;
      const stimStatus = store.state.stimulation.stimStatus;

      expect(updatedStatuses).toStrictEqual(initialStatuses);
      expect(stimStatus).toBe(STIM_STATUS.SHORT_CIRCUIT_ERROR);
    });

    test("When backend emits stimulatorCircuitStatus message with no short  errors, Then ws client updates stim status to config check complete and set indices to data state", async () => {
      // confirm precondition
      const initialStatuses = store.state.stimulation.stimulatorCircuitStatuses;
      expect(initialStatuses).toHaveLength(0);

      const stimulatorStatuses = new Array(24).fill("open", 0, 10).fill("media", 10, 24);

      await new Promise((resolve) => {
        socketServerSide.emit("stimulator_circuit_statuses", JSON.stringify(stimulatorStatuses), (ack) => {
          resolve(ack);
        });
      });

      const updatedStatuses = store.state.stimulation.stimulatorCircuitStatuses;
      const stimStatus = store.state.stimulation.stimStatus;

      expect(updatedStatuses).toStrictEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
      expect(stimStatus).toBe(STIM_STATUS.CONFIG_CHECK_COMPLETE);
    });

    test("When backend emits swUpdate message with allowSoftwareUpdate value, Then ws client commits value to store", async () => {
      const message = {
        allowSoftwareUpdate: true,
      };

      // confirm precondition
      expect(store.state.system.allowSWUpdateInstall).toBe(false);

      await new Promise((resolve) => {
        socketServerSide.emit("sw_update", JSON.stringify(message), (ack) => {
          resolve(ack);
        });
      });
      expect(store.state.system.allowSWUpdateInstall).toBe(true);
    });
    test("When backend emits swUpdate message with softwareUpdateAvailable value, Then ws client commits value to store", async () => {
      const message = {
        softwareUpdateAvailable: true,
      };

      // confirm precondition
      expect(store.state.system.softwareUpdateAvailable).toBe(false);

      await new Promise((resolve) => {
        socketServerSide.emit("sw_update", JSON.stringify(message), (ack) => {
          resolve(ack);
        });
      });
      expect(store.state.system.softwareUpdateAvailable).toBe(true);
    });
    test("When backend emits fwUpdate message with firmwareUpdateAvailable true, Then ws client commits value to store", async () => {
      const message = {
        firmwareUpdateAvailable: true,
        channelFwUpdate: true,
      };

      // confirm precondition
      expect(store.state.system.firmwareUpdateAvailable).toBe(false);
      expect(store.state.system.firmwareUpdateDurMins).toBeNull();

      await new Promise((resolve) => {
        socketServerSide.emit("fw_update", JSON.stringify(message), (ack) => {
          resolve(ack);
        });
      });
      expect(store.state.system.firmwareUpdateAvailable).toBe(true);
      expect(store.state.system.firmwareUpdateDurMins).toBe(5);
    });
    test("When backend emits fwUpdate message with firmwareUpdateAvailable false, Then ws client does not commit value to store", async () => {
      const message = {
        firmwareUpdateAvailable: false,
      };

      // confirm precondition
      expect(store.state.system.firmwareUpdateAvailable).toBe(false);
      expect(store.state.system.firmwareUpdateDurMins).toBeNull();

      await new Promise((resolve) => {
        socketServerSide.emit("fw_update", JSON.stringify(message), (ack) => {
          resolve(ack);
        });
      });
      expect(store.state.system.firmwareUpdateAvailable).toBe(false);
      expect(store.state.system.firmwareUpdateDurMins).toBeNull();
    });
    test("When backend emits promptUserInput message with customerCreds as input type, Then ws client sets correct flag in store", async () => {
      const message = {
        inputType: "userCreds",
      };

      // confirm precondition
      expect(store.state.settings.userCredInputNeeded).toBe(false);

      await new Promise((resolve) => {
        socketServerSide.emit("prompt_user_input", JSON.stringify(message), (ack) => {
          resolve(ack);
        });
      });
      expect(store.state.settings.userCredInputNeeded).toBe(true);
    });

    test.each([
      ["plateBarcode", "ML2022002001", validPlateBarcodeOld, true],
      ["plateBarcode", "ML2022002001", validPlateBarcodeBeta2, true],
      ["plateBarcode", "ML2022002001", validPlateBarcodeBeta1, false],
      ["stimBarcode", "MS2022002001", validStimBarcodeOld, true],
    ])(
      "Given barcode is not in manual mode, When backend emits barcode message with valid %s, Then ws client updates correct barcode in store",
      async (barcodeType, oldBarcode, validBarcode, beta2Mode) => {
        const message = {
          [barcodeType]: validBarcode,
        };
        await store.commit("system/setBarcodeManualMode", false);
        await store.commit("system/setBarcode", {
          type: barcodeType,
          newValue: oldBarcode,
          isValid: true,
        });

        // confirm precondition
        expect(store.state.system.barcodes[barcodeType].value).toBe(oldBarcode);

        await new Promise((resolve) => {
          socketServerSide.emit("barcode", JSON.stringify(message), (ack) => {
            resolve(ack);
          });
        });

        const stimConfigState = store.state.stimulation.stimStatus === STIM_STATUS.NO_PROTOCOLS_ASSIGNED;

        expect(store.state.system.barcodes[barcodeType].value).toBe(validBarcode);
        expect(store.state.system.barcodes[barcodeType].valid).toBe(true);
        expect(stimConfigState).toBe(true);
      }
    );
    test.each([
      ["plateBarcode", validPlateBarcodeOld],
      ["stimBarcode", validStimBarcodeOld],
    ])(
      "Given barcode is in manual mode, When backend emits barcode message with valid %s, Then ws client does not set new barcode in store",
      async (barcodeType, validBarcode) => {
        const message = {
          barcodeType: validBarcode,
        };

        store.commit("system/setBarcodeManualMode", true);

        // confirm precondition
        expect(store.state.system.barcodes[barcodeType].value).toBeNull();

        await new Promise((resolve) => {
          socketServerSide.emit("barcode", JSON.stringify(message), (ack) => {
            resolve(ack);
          });
        });
        expect(store.state.playback.barcodes[barcodeType].value).toBeNull();
      }
    );
    test.each([
      "InstrumentCreateConnectionError",
      "InstrumentConnectionLostError",
      "InstrumentBadDataError",
      "InstrumentFirmwareError",
      "FirmwareAndSoftwareNotCompatibleError",
    ])(
      "When backend emits error messages %s, Then it will update the shutdown error status in settings state",
      async (errorType) => {
        expect(store.state.system.shutdownErrorStatus).toBe("");

        const latestCompatibleSwVersion =
          errorType === "FirmwareAndSoftwareNotCompatibleError" ? "1.2.3" : null;

        await new Promise((resolve) => {
          socketServerSide.emit("error", JSON.stringify({ errorType, latestCompatibleSwVersion }), (ack) => {
            resolve(ack);
          });
        });

        const additionalText = latestCompatibleSwVersion
          ? ". Please download the installer for the correct version here:"
          : ". Stingray Controller is about to shutdown.";

        expect(store.state.system.shutdownErrorStatus).toBe(ERRORS[errorType] + additionalText);
      }
    );
  });
});
