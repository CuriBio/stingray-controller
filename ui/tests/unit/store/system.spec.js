import Vuex from "vuex";
import { createLocalVue } from "@vue/test-utils";
// import { STIM_STATUS } from "@/store/modules/stimulation/enums";
// import { socket as socketClientSide } from "@/store/plugins/websocket";
// import { ERRORS } from "../../../store/modules/settings/enums.js";

// const validPlateBarcodeOld = "ML2022001000";
// const validPlateBarcodeBeta1 = "ML22001000-1";
// const validPlateBarcodeBeta2 = "ML22001000-2";
// const validStimBarcodeOld = "MS2022001000";

// const http = require("http");
// const ioServer = require("socket.io");

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
      (update) => {
        store.commit("system/setFirmwareUpdateAvailable", update);
        expect(store.state.system.firmwareUpdateDurMins).toStrictEqual(update ? 5 : 1);
        expect(store.state.system.firmwareUpdateAvailable).toStrictEqual(true);
      }
    );

    describe("Barcode validity", () => {
      test.each([
        ["", "error due to empty string", false],
        ["ML34567890123", "error due tolength over 12", false],
        ["ML345678901", "error due tolength under 12", false],
        ["ML二千万一千〇九", "error due to all unicode", false],
        ["ML2021$72144", "error due to invalid character '$'", false],
        ["ML2020172144", "error due to invalid year '2020'", false],
        ["ML2021000144", "error due to invalid Julian date '000'", false],
        ["ML2021367144", "error due to invalid Julian date '367'", false],
        ["MS2021172000", "header 'MS'", false],
        ["ML2021172001", "valid kit ID '001'", true],
        ["ML2021172002", "valid kit ID '002'", true],
        ["ML2021172003", "valid kit ID '003'", true],
        ["ML2021172004", "valid kit ID '004'", true],
        ["ML9999172001", "year '9999'", true],
        ["ML2021001144", "julian date '001'", true],
        ["ML2021366144", "julian date '366'", true],
      ])(
        "Given a plate barcode scanned results in value %s, When validation rule FAILS  or PASSES due %s, Then validation results set valid to %s",
        async (plateBarcode, reason, valid) => {
          // testing with plate barcode here but the functionality is exactly the same for stim barcodes
          store.dispatch("system/validateBarcode", { type: "plateBarcode", newValue: plateBarcode });
          expect(store.state.system.barcodes.plateBarcode.valid).toBe(valid);
        }
      );
    });
  });
  // describe("websocket", () => {
  //   let httpServer;
  //   let wsServer;
  //   let socketServerSide;

  //   beforeAll((done) => {
  //     httpServer = http.createServer().listen(4565); // TODO use constant here
  //     wsServer = ioServer(httpServer);
  //     // wait for connection
  //     wsServer.on("connect", (socket) => {
  //       socketServerSide = socket;
  //       done();
  //     });
  //   });

  //   afterEach(() => {
  //     // event handlers persist through tests, so clear them all after each test
  //     socketClientSide.off();
  //   });

  //   afterAll(() => {
  //     if (socketServerSide.connected) {
  //       socketServerSide.disconnect();
  //     }
  //     wsServer.close();
  //     httpServer.close();
  //   });

  //   test("Given ws client has a 'message' event handler, When ws server emits a 'message' event, Then client receives message", async () => {
  //     // Sanity test for websockets
  //     const expectedMessage = "Test Message";

  //     await new Promise((resolve) => {
  //       socketClientSide.on("message", (message) => {
  //         expect(message).toBe(expectedMessage);
  //         resolve();
  //       });
  //       socketServerSide.send(expectedMessage);
  //     });
  //   });

  //   test("When backend emits stimulatorCircuitStatus message with short circuit errors, Then ws client updates stim status to short circuit error", async () => {
  //     // confirm precondition
  //     const initialStatuses = store.state.stimulation.stimulatorCircuitStatuses;
  //     expect(initialStatuses).toHaveLength(0);

  //     const stimulatorStatuses = new Array(24)
  //       .fill("open", 0, 10)
  //       .fill("media", 10, 20)
  //       .fill("short", 20, 24);

  //     const stimulatorStatusesObj = {};
  //     stimulatorStatuses.map((status, wellIdx) => {
  //       stimulatorStatusesObj[`${wellIdx}`] = status;
  //     });

  //     await new Promise((resolve) => {
  //       socketServerSide.emit("stimulatorCircuitStatuses", JSON.stringify(stimulatorStatusesObj), (ack) => {
  //         resolve(ack);
  //       });
  //     });

  //     const updatedStatuses = store.state.stimulation.stimulatorCircuitStatuses;
  //     const stimStatus = store.state.stimulation.stimStatus;

  //     expect(updatedStatuses).toStrictEqual(initialStatuses);
  //     expect(stimStatus).toBe(STIM_STATUS.SHORT_CIRCUIT_ERROR);
  //   });

  //   test("When backend emits stimulatorCircuitStatus message with error status, Then ws client updates stim status to short circuit error", async () => {
  //     // confirm precondition
  //     const initialStatuses = store.state.stimulation.stimulatorCircuitStatuses;
  //     expect(initialStatuses).toHaveLength(0);

  //     const stimulatorStatuses = new Array(24)
  //       .fill("open", 0, 10)
  //       .fill("media", 10, 20)
  //       .fill("error", 20, 24);

  //     await new Promise((resolve) => {
  //       socketServerSide.emit("stimulatorCircuitStatuses", JSON.stringify(stimulatorStatuses), (ack) => {
  //         resolve(ack);
  //       });
  //     });

  //     const updatedStatuses = store.state.stimulation.stimulatorCircuitStatuses;
  //     const stimStatus = store.state.stimulation.stimStatus;

  //     expect(updatedStatuses).toStrictEqual(initialStatuses);
  //     expect(stimStatus).toBe(STIM_STATUS.SHORT_CIRCUIT_ERROR);
  //   });

  //   test("When backend emits stimulatorCircuitStatus message with no short  errors, Then ws client updates stim status to config check complete and set indices to data state", async () => {
  //     // confirm precondition
  //     const initialStatuses = store.state.stimulation.stimulatorCircuitStatuses;
  //     expect(initialStatuses).toHaveLength(0);

  //     const stimulatorStatuses = new Array(24).fill("open", 0, 10).fill("media", 10, 24);

  //     await new Promise((resolve) => {
  //       socketServerSide.emit("stimulatorCircuitStatuses", JSON.stringify(stimulatorStatuses), (ack) => {
  //         resolve(ack);
  //       });
  //     });

  //     const updatedStatuses = store.state.stimulation.stimulatorCircuitStatuses;
  //     const stimStatus = store.state.stimulation.stimStatus;

  //     expect(updatedStatuses).toStrictEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
  //     expect(stimStatus).toBe(STIM_STATUS.CONFIG_CHECK_COMPLETE);
  //   });

  //   test("When backend emits swUpdate message with allowSoftwareUpdate value, Then ws client commits value to store", async () => {
  //     const message = {
  //       allowSoftwareUpdate: true,
  //     };

  //     // confirm precondition
  //     expect(store.state.system.allowSwUpdateInstall).toBe(false);

  //     await new Promise((resolve) => {
  //       socketServerSide.emit("swUpdate", JSON.stringify(message), (ack) => {
  //         resolve(ack);
  //       });
  //     });
  //     expect(store.state.system.allowSwUpdateInstall).toBe(true);
  //   });
  //   test("When backend emits swUpdate message with softwareUpdateAvailable value, Then ws client commits value to store", async () => {
  //     const message = {
  //       softwareUpdateAvailable: true,
  //     };

  //     // confirm precondition
  //     expect(store.state.system.softwareUpdateAvailable).toBe(false);

  //     await new Promise((resolve) => {
  //       socketServerSide.emit("swUpdate", JSON.stringify(message), (ack) => {
  //         resolve(ack);
  //       });
  //     });
  //     expect(store.state.system.softwareUpdateAvailable).toBe(true);
  //   });
  //   test("When backend emits fwUpdate message with firmwareUpdateAvailable true, Then ws client commits value to store", async () => {
  //     const message = {
  //       firmwareUpdateAvailable: true,
  //       channelFwUpdate: true,
  //     };

  //     // confirm precondition
  //     expect(store.state.system.firmwareUpdateAvailable).toBe(false);
  //     expect(store.state.system.firmwareUpdateDurMins).toBeNull();

  //     await new Promise((resolve) => {
  //       socketServerSide.emit("fwUpdate", JSON.stringify(message), (ack) => {
  //         resolve(ack);
  //       });
  //     });
  //     expect(store.state.system.firmwareUpdateAvailable).toBe(true);
  //     expect(store.state.system.firmwareUpdateDurMins).toBe(5);
  //   });
  //   test("When backend emits fwUpdate message with firmwareUpdateAvailable false, Then ws client does not commit value to store", async () => {
  //     const message = {
  //       firmwareUpdateAvailable: false,
  //     };

  //     // confirm precondition
  //     expect(store.state.system.firmwareUpdateAvailable).toBe(false);
  //     expect(store.state.system.firmwareUpdateDurMins).toBeNull();

  //     await new Promise((resolve) => {
  //       socketServerSide.emit("fwUpdate", JSON.stringify(message), (ack) => {
  //         resolve(ack);
  //       });
  //     });
  //     expect(store.state.system.firmwareUpdateAvailable).toBe(false);
  //     expect(store.state.system.firmwareUpdateDurMins).toBeNull();
  //   });
  //   test("When backend emits promptUserInput message with customerCreds as input type, Then ws client sets correct flag in store", async () => {
  //     const message = {
  //       inputType: "userCreds",
  //     };

  //     // confirm precondition
  //     expect(store.state.settings.userCredInputNeeded).toBe(false);

  //     await new Promise((resolve) => {
  //       socketServerSide.emit("promptUserInput", JSON.stringify(message), (ack) => {
  //         resolve(ack);
  //       });
  //     });
  //     expect(store.state.settings.userCredInputNeeded).toBe(true);
  //   });

  //   test.each([
  //     ["plateBarcode", "ML2022002001", validPlateBarcodeOld, true],
  //     ["plateBarcode", "ML2022002001", validPlateBarcodeBeta2, true],
  //     ["plateBarcode", "ML2022002001", validPlateBarcodeBeta1, false],
  //     ["stimBarcode", "MS2022002001", validStimBarcodeOld, true],
  //   ])(
  //     "Given barcode is not in manual mode, When backend emits barcode message with valid %s, Then ws client updates correct barcode in store",
  //     async (barcodeType, oldBarcode, validBarcode, beta2Mode) => {
  //       const message = {
  //         [barcodeType]: validBarcode,
  //       };
  //       await store.commit("system/setBarcodeManualMode", false);
  //       await store.commit("system/setBarcode", {
  //         type: barcodeType,
  //         newValue: oldBarcode,
  //         isValid: true,
  //       });

  //       // confirm precondition
  //       expect(store.state.system.barcodes[barcodeType].value).toBe(oldBarcode);

  //       await new Promise((resolve) => {
  //         socketServerSide.emit("barcode", JSON.stringify(message), (ack) => {
  //           resolve(ack);
  //         });
  //       });

  //       const stimConfigState = store.state.stimulation.stimStatus === STIM_STATUS.NO_PROTOCOLS_ASSIGNED;

  //       expect(store.state.system.barcodes[barcodeType].value).toBe(validBarcode);
  //       expect(store.state.system.barcodes[barcodeType].valid).toBe(true);
  //       expect(stimConfigState).toBe(true);
  //     }
  //   );
  //   test.each([
  //     ["plateBarcode", validPlateBarcodeOld],
  //     ["stimBarcode", validStimBarcodeOld],
  //   ])(
  //     "Given barcode is in manual mode, When backend emits barcode message with valid %s, Then ws client does not set new barcode in store",
  //     async (barcodeType, validBarcode) => {
  //       const message = {
  //         barcodeType: validBarcode,
  //       };

  //       store.commit("system/setBarcodeManualMode", true);

  //       // confirm precondition
  //       expect(store.state.system.barcodes[barcodeType].value).toBeNull();

  //       await new Promise((resolve) => {
  //         socketServerSide.emit("barcode", JSON.stringify(message), (ack) => {
  //           resolve(ack);
  //         });
  //       });
  //       expect(store.state.playback.barcodes[barcodeType].value).toBeNull();
  //     }
  //   );
  //   test.each([
  //     "InstrumentCreateConnectionError",
  //     "InstrumentConnectionLostError",
  //     "InstrumentBadDataError",
  //     "InstrumentFirmwareError",
  //     "FirmwareAndSoftwareNotCompatibleError",
  //   ])(
  //     "When backend emits error messages %s, Then it will update the shutdown error status in settings state",
  //     async (errorType) => {
  //       expect(store.state.system.systemErrorCode).toBe("");

  //       const latestCompatibleSwVersion =
  //         errorType === "FirmwareAndSoftwareNotCompatibleError" ? "1.2.3" : null;

  //       await new Promise((resolve) => {
  //         socketServerSide.emit("error", JSON.stringify({ errorType, latestCompatibleSwVersion }), (ack) => {
  //           resolve(ack);
  //         });
  //       });

  //       const additionalText = latestCompatibleSwVersion
  //         ? ". Please download the installer for the correct version here:"
  //         : ". Stingray Controller is about to shutdown.";

  //       expect(store.state.system.systemErrorCode).toBe(ERRORS[errorType] + additionalText);
  //     }
  //   );
  // });
});
