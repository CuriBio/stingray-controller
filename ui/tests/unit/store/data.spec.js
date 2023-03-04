import Vuex from "vuex";
import { createLocalVue } from "@vue/test-utils";
import axios from "axios";
const MockAxiosAdapter = require("axios-mock-adapter");
import { system_status_regexp } from "@/store/modules/flask/url_regex";
import { STATUS } from "@/store/modules/flask/enums";
import { STIM_STATUS } from "@/store/modules/stimulation/enums";
import { socket as socket_client_side } from "@/store/plugins/websocket";
import { arry, new_arry } from "../js-utils/waveform_data_provider.js";
import { ping_system_status } from "@/store/modules/flask/actions";
import { ERRORS } from "../../../store/modules/settings/enums.js";

const valid_plateBarcode_old = "ML2022001000";
const valid_plateBarcode_beta_1 = "ML22001000-1";
const valid_plateBarcode_beta_2 = "ML22001000-2";
const valid_stimBarcode_old = "MS2022001000";

const http = require("http");
const io_server = require("socket.io");

describe("store/data", () => {
  const localVue = createLocalVue();
  localVue.use(Vuex);
  let NuxtStore;
  let store;
  let ar;
  let nr;

  beforeAll(async () => {
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
    // event handlers persist through tests, so clear them all before any tests in this file run
    socket_client_side.off();
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
    // some tests modify these two values, so make a deep copy before each test
    ar = JSON.parse(JSON.stringify(arry));
    nr = JSON.parse(JSON.stringify(new_arry));
    store.commit("waveform/set_x_axis_zoom_levels", [
      { x_scale: 30 * 1e6 },
      { x_scale: 15 * 1e6 },
      { x_scale: 5 * 1e6 },
      { x_scale: 2 * 1e6 },
      { x_scale: 1 * 1e6 },
    ]);
  });

  afterEach(() => {
    // event handlers persist through tests, so clear them all after each test
    socket_client_side.off();
  });

  test("When initialized, Then the plate_waveforms is an empty representation of a 96-well plate", () => {
    const array_of_waveforms = store.state.data.plate_waveforms;
    expect(array_of_waveforms).toHaveLength(96);
    expect(array_of_waveforms[0]).toStrictEqual(
      expect.objectContaining({
        x_data_points: [],
        y_data_points: [],
      })
    );
    expect(array_of_waveforms[95]).toStrictEqual(
      expect.objectContaining({
        x_data_points: [],
        y_data_points: [],
      })
    );
  });

  describe("mutations/getters", () => {
    test("Given some values in plate_waveforms, When the clear_plate_waveforms mutation is committed, Then plate_waveforms becomes empty x/y data points array", () => {
      store.commit("data/set_plate_waveforms", [
        { x_data_points: [1], y_data_points: [2] },
        { x_data_points: [1], y_data_points: [2] },
      ]);

      store.commit("data/clear_plate_waveforms");
      expect(store.state.data.plate_waveforms).toHaveLength(2);
      expect(store.state.data.plate_waveforms[0].x_data_points).toHaveLength(0);
      expect(store.state.data.plate_waveforms[0].y_data_points).toHaveLength(0);
      expect(store.state.data.plate_waveforms[1].x_data_points).toHaveLength(0);
      expect(store.state.data.plate_waveforms[1].y_data_points).toHaveLength(0);
    });

    test("When tissue waveforms get appended and stim is active, Then the stim waveforms will get updated with latest tissue data timepoint", async () => {
      const test_stim = {
        0: [
          [5000, 10000],
          [0, 1],
        ],
        1: [[11000], [1]],
      };

      await store.dispatch("data/append_stim_waveforms", test_stim);
      expect(store.state.data.stim_fill_assignments).toStrictEqual(
        [
          [
            [
              0,
              [
                [5000, 101000],
                [10000, 101000],
              ],
            ],
            [
              1,
              [
                [10000, 101000],
                [10000, 101000],
              ],
            ],
          ],
          [
            [
              1,
              [
                [11000, 101000],
                [11000, 101000],
              ],
            ],
          ],
        ].concat(new Array(94).fill([]))
      );

      const tissue_arr = {
        waveform_data: {
          basic_data: {
            waveform_data_points: {
              0: {
                x_data_points: [13000],
                y_data_points: [20],
              },
              1: {
                x_data_points: [13000],
                y_data_points: [50],
              },
            },
          },
        },
      };
      await store.dispatch("data/append_plate_waveforms", tissue_arr);
      expect(store.state.data.stim_fill_assignments).toStrictEqual(
        [
          [
            [
              0,
              [
                [5000, 101000],
                [10000, 101000],
              ],
            ],
            [
              1,
              [
                [10000, 101000],
                [13000, 101000],
              ],
            ],
          ],
          [
            [
              1,
              [
                [11000, 101000],
                [13000, 101000],
              ],
            ],
          ],
        ].concat(new Array(94).fill([]))
      );
    });

    test("When plate_waveforms is initially mutated with few data points, Then subsequent mutations append data points to the existing plate_waveforms", async () => {
      store.commit("data/set_plate_waveforms", ar);

      const stored_waveform = store.getters["data/plate_waveforms"];
      expect(stored_waveform).toHaveLength(24);
      expect(stored_waveform[0].x_data_points).toHaveLength(4);

      await store.dispatch("data/append_plate_waveforms", nr);
      expect(store.state.data.plate_waveforms).toHaveLength(24);
      expect(store.state.data.plate_waveforms[0].x_data_points).toHaveLength(8);
      // Tanner (12/20/21): There was a bug where stored_waveform was being changed from an array to an object in append_plate_waveforms, so adding this assertion to prevent that
      expect(Array.isArray(store.state.data.plate_waveforms)).toBe(true);
    });

    test("When mutating heatmap_values, Then getting heatmap_values should return mutated value", async () => {
      const test = {
        "Twitch Force": { data: [0] },
        "Twitch Period": { data: [1] },
        "Twitch Frequency": { data: [2] },
        "Twitch Width 80": { data: [3] },
        "Contraction Velocity": { data: [4] },
        "Relaxation Velocity": { data: [5] },
      };
      store.commit("data/set_heatmap_values", test);
      expect(store.getters["data/heatmap_values"]["Twitch Frequency"]).toStrictEqual({ data: [2] });
    });

    test("When mutating heatmap data at value, Then the data at value in state should return mutated data array", async () => {
      const test = {
        "Twitch Force": { data: [[], [], [], []] },
      };
      store.commit("data/set_heatmap_values", test);
      store.commit("data/set_metric_data", {
        name: "Twitch Force",
        data: [1, 2, 3, 4],
      });
      store.state.data.heatmap_values["Twitch Force"].data.map((well) => {
        expect(well).toHaveLength(1);
      });
    });
  });

  test("Given some values in stim_waveforms, When the clear_stim_waveforms mutation is committed, Then stim_waveforms becomes empty x/y data points array", () => {
    store.commit("data/set_stim_waveforms", [
      { x_data_points: [1], y_data_points: [2] },
      { x_data_points: [1], y_data_points: [2] },
    ]);
    expect(store.state.data.stim_waveforms).toHaveLength(2);
    expect(store.state.data.stim_waveforms).toHaveLength(2);
    expect(store.state.data.stim_waveforms[0].x_data_points).toHaveLength(1);
    expect(store.state.data.stim_waveforms[0].y_data_points).toHaveLength(1);
    expect(store.state.data.stim_waveforms[1].x_data_points).toHaveLength(1);
    expect(store.state.data.stim_waveforms[1].y_data_points).toHaveLength(1);

    store.commit("data/clear_stim_waveforms");
    expect(store.state.data.stim_waveforms).toHaveLength(2);
    expect(store.state.data.stim_waveforms[0].x_data_points).toHaveLength(0);
    expect(store.state.data.stim_waveforms[0].y_data_points).toHaveLength(0);
    expect(store.state.data.stim_waveforms[1].x_data_points).toHaveLength(0);
    expect(store.state.data.stim_waveforms[1].y_data_points).toHaveLength(0);
  });

  test("When stim_waveforms is initially mutated with few data points, Then subsequent mutations append data points to the existing stim_waveforms", async () => {
    store.commit("data/set_stim_waveforms", [
      { x_data_points: [11, 12], y_data_points: [0, 0] },
      { x_data_points: [21], y_data_points: [0] },
      { x_data_points: [], y_data_points: [] },
    ]);

    const stored_waveform = store.getters["data/stim_waveforms"];

    store.dispatch("data/append_stim_waveforms", {
      0: [[13], [99]],
      2: [
        [211, 212],
        [999, 999],
      ],
    });

    expect(stored_waveform).toHaveLength(3);
    expect(stored_waveform[0]).toStrictEqual({
      x_data_points: [11, 12, 13],
      y_data_points: [0, 0, 101000],
    });
    expect(stored_waveform[1]).toStrictEqual({
      x_data_points: [21],
      y_data_points: [0],
    });
    expect(stored_waveform[2]).toStrictEqual({
      x_data_points: [211, 212],
      y_data_points: [101000, 101000],
    });
  });
  test("Given stim_fill_assignments already has values for at least one subprotocol for a well, When a data for a single new subprotocol is appended, Then the end timepoint of the first subprotocol is updated to the start timepoint of the new subprotocol", async () => {
    store.dispatch("data/append_stim_waveforms", { 0: [[0], [0]] });

    // confirm precondition
    expect(store.state.data.stim_fill_assignments[0]).toStrictEqual([
      [
        0,
        [
          [0, 101000],
          [0, 101000],
        ],
      ],
    ]);

    store.dispatch("data/append_stim_waveforms", { 0: [[10], [1]] });

    // make sure new valadded to stim_fill_assignments and prev val updated correctly
    expect(store.state.data.stim_fill_assignments[0]).toStrictEqual([
      [
        0,
        [
          [0, 101000],
          [10, 101000],
        ],
      ],
      [
        1,
        [
          [10, 101000],
          [10, 101000],
        ],
      ],
    ]);
  });

  describe("websocket", () => {
    let http_server;
    let ws_server;
    let socket_server_side;
    beforeEach(() => {
      store.commit("waveform/set_x_axis_zoom_levels", [
        { x_scale: 30 * 1e6 },
        { x_scale: 15 * 1e6 },
        { x_scale: 5 * 1e6 },
        { x_scale: 2 * 1e6 },
        { x_scale: 1 * 1e6 },
      ]);
    });
    beforeAll((done) => {
      http_server = http.createServer().listen(4567); // TODO use constant here
      ws_server = io_server(http_server);
      // wait for connection
      ws_server.on("connect", (socket) => {
        socket_server_side = socket;
        done();
      });
    });

    afterAll(() => {
      if (socket_server_side.connected) {
        socket_server_side.disconnect();
      }
      ws_server.close();
      http_server.close();
    });

    test("Given ws client has a 'message' event handler, When ws server emits a 'message' event, Then client receives message", async () => {
      // Sanity test for websockets
      const expected_message = "Test Message";

      await new Promise((resolve) => {
        socket_client_side.on("message", (message) => {
          expect(message).toEqual(expected_message);
          resolve();
        });
        socket_server_side.send(expected_message);
      });
    });
    test("When h5 files are detected by desktop app, Then client show error", async () => {
      // empty array to represent the corrupt files.
      const expected_message = JSON.stringify([]);
      expect(store.state.data.h5_warning).toBe(false);

      await new Promise((resolve) => {
        socket_server_side.emit("corrupt_files_alert", expected_message, (ack) => {
          resolve(ack);
        });
      });
      expect(store.state.data.h5_warning).toBe(true);
    });

    test("When backend emits stimulation message, Then ws client updates stim_waveforms", async () => {
      store.commit("data/set_stim_waveforms", [
        { x_data_points: [1], y_data_points: [2] },
        { x_data_points: [3], y_data_points: [4] },
      ]);

      const stored_stim_data = store.getters["data/stim_waveforms"];
      expect(stored_stim_data).toHaveLength(2);
      expect(stored_stim_data[0].x_data_points).toHaveLength(1);

      const new_stim_data = {
        0: [
          [2, 3],
          [5, 6],
        ],
        1: [[8], [10]],
      };

      await new Promise((resolve) => {
        socket_server_side.emit("stimulation_data", JSON.stringify(new_stim_data), (ack) => {
          resolve(ack);
        });
      });

      expect(stored_stim_data).toHaveLength(2);
      expect(stored_stim_data[0]).toStrictEqual({
        x_data_points: [1, 2, 3],
        y_data_points: [2, 101000, 101000],
      });
      expect(stored_stim_data[1]).toStrictEqual({
        x_data_points: [3, 8],
        y_data_points: [4, 101000],
      });
    });

    test("When backend emits stimulator_circuit_status message with short circuit errors, Then ws client updates stim status to short circuit error", async () => {
      // confirm precondition
      const initial_statuses = store.state.data.stimulatorCircuitStatuses;
      expect(initial_statuses).toHaveLength(0);

      const stimulatorStatuses = new Array(24)
        .fill("open", 0, 10)
        .fill("media", 10, 20)
        .fill("short", 20, 24);

      const stimulatorStatusesObj = {};
      stimulatorStatuses.map((status, well_idx) => {
        stimulatorStatusesObj[`${well_idx}`] = status;
      });

      await new Promise((resolve) => {
        socket_server_side.emit("stimulatorCircuitStatuses", JSON.stringify(stimulatorStatusesObj), (ack) => {
          resolve(ack);
        });
      });

      const updated_statuses = store.state.data.stimulatorCircuitStatuses;
      const stimStatus = store.state.stimulation.stim_status;

      expect(updated_statuses).toStrictEqual(initial_statuses);
      expect(stim_status).toBe(STIM_STATUS.SHORT_CIRCUIT_ERROR);
    });

    test("When backend emits stimulator_circuit_status message with error status, Then ws client updates stim status to short circuit error", async () => {
      // confirm precondition
      const initial_statuses = store.state.data.stimulatorCircuitStatuses;
      expect(initial_statuses).toHaveLength(0);

      const stimulatorStatuses = new Array(24)
        .fill("open", 0, 10)
        .fill("media", 10, 20)
        .fill("error", 20, 24);

      await new Promise((resolve) => {
        socket_server_side.emit("stimulatorCircuitStatuses", JSON.stringify(stimulatorStatuses), (ack) => {
          resolve(ack);
        });
      });

      const updated_statuses = store.state.data.stimulatorCircuitStatuses;
      const stimStatus = store.state.stimulation.stim_status;

      expect(updated_statuses).toStrictEqual(initial_statuses);
      expect(stim_status).toBe(STIM_STATUS.SHORT_CIRCUIT_ERROR);
    });

    test("When backend emits stimulator_circuit_status message with no short  errors, Then ws client updates stim status to config check complete and set indices to data state", async () => {
      // confirm precondition
      const initial_statuses = store.state.data.stimulatorCircuitStatuses;
      expect(initial_statuses).toHaveLength(0);

      const stimulatorStatuses = new Array(24).fill("open", 0, 10).fill("media", 10, 24);

      await new Promise((resolve) => {
        socket_server_side.emit("stimulatorCircuitStatuses", JSON.stringify(stimulatorStatuses), (ack) => {
          resolve(ack);
        });
      });

      const updated_statuses = store.state.data.stimulatorCircuitStatuses;
      const stimStatus = store.state.stimulation.stim_status;

      expect(updated_statuses).toStrictEqual([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
      expect(stim_status).toBe(STIM_STATUS.CONFIG_CHECK_COMPLETE);
    });
    test("When backend emits status update message with no error, Then ws client updates file count", async () => {
      const new_status_update = {
        file_name: "test_filename",
      };

      await new Promise((resolve) => {
        socket_server_side.emit("upload_status", JSON.stringify(new_status_update), (ack) => {
          resolve(ack);
        });
      });

      const { total_uploaded_files, upload_error, file_count } = store.state.settings;

      expect(total_uploaded_files[0]).toBe(new_status_update.file_name);
      expect(upload_error).toBe(false);
      expect(file_count).toBe(1);
    });

    test("When backend emits status update message with an upload error, Then ws client does not update file count and sets upload_error status to true", async () => {
      const new_status_update = {
        file_name: "test_filename",
        error: "upload_error",
      };

      await new Promise((resolve) => {
        socket_server_side.emit("upload_status", JSON.stringify(new_status_update), (ack) => {
          resolve(ack);
        });
      });

      const { total_uploaded_files, upload_error, file_count } = store.state.settings;

      expect(total_uploaded_files[0]).toBe(new_status_update.file_name);
      expect(upload_error).toBe(true);
      expect(file_count).toBe(0);
    });
    test("When backend emits sw_update message with allow_software_update value, Then ws client commits value to store", async () => {
      const message = {
        allow_software_update: true,
      };

      // confirm precondition
      expect(store.state.settings.allowSWUpdateInstall).toBe(false);

      await new Promise((resolve) => {
        socket_server_side.emit("sw_update", JSON.stringify(message), (ack) => {
          resolve(ack);
        });
      });
      expect(store.state.settings.allowSWUpdateInstall).toBe(true);
    });
    test("When backend emits sw_update message with softwareUpdateAvailable value, Then ws client commits value to store", async () => {
      const message = {
        softwareUpdateAvailable: true,
      };

      // confirm precondition
      expect(store.state.settings.softwareUpdateAvailable).toBe(false);

      await new Promise((resolve) => {
        socket_server_side.emit("sw_update", JSON.stringify(message), (ack) => {
          resolve(ack);
        });
      });
      expect(store.state.settings.softwareUpdateAvailable).toBe(true);
    });
    test("When backend emits fw_update message with firmwareUpdateAvailable true, Then ws client commits value to store", async () => {
      const message = {
        firmwareUpdateAvailable: true,
        channel_fw_update: true,
      };

      // confirm precondition
      expect(store.state.settings.firmwareUpdateAvailable).toBe(false);
      expect(store.state.settings.firmwareUpdateDurMins).toBeNull();

      await new Promise((resolve) => {
        socket_server_side.emit("fw_update", JSON.stringify(message), (ack) => {
          resolve(ack);
        });
      });
      expect(store.state.settings.firmwareUpdateAvailable).toBe(true);
      expect(store.state.settings.firmwareUpdateDurMins).toBe(5);
    });
    test("When backend emits fw_update message with firmwareUpdateAvailable false, Then ws client does not commit value to store", async () => {
      const message = {
        firmwareUpdateAvailable: false,
      };

      // confirm precondition
      expect(store.state.settings.firmwareUpdateAvailable).toBe(false);
      expect(store.state.settings.firmwareUpdateDurMins).toBeNull();

      await new Promise((resolve) => {
        socket_server_side.emit("fw_update", JSON.stringify(message), (ack) => {
          resolve(ack);
        });
      });
      expect(store.state.settings.firmwareUpdateAvailable).toBe(false);
      expect(store.state.settings.firmwareUpdateDurMins).toBeNull();
    });
    test("When backend emits prompt_user_input message with customer_creds as input type, Then ws client sets correct flag in store", async () => {
      const message = {
        input_type: "user_creds",
      };

      // confirm precondition
      expect(store.state.settings.user_cred_input_needed).toBe(false);

      await new Promise((resolve) => {
        socket_server_side.emit("prompt_user_input", JSON.stringify(message), (ack) => {
          resolve(ack);
        });
      });
      expect(store.state.settings.user_cred_input_needed).toBe(true);
    });

    test.each([
      ["plateBarcode", "ML2022002001", valid_plateBarcode_old, true],
      ["plateBarcode", "ML2022002001", valid_plateBarcode_beta_2, true],
      ["plateBarcode", "ML2022002001", valid_plateBarcode_beta_1, false],
      ["stimBarcode", "MS2022002001", valid_stimBarcode_old, true],
    ])(
      "Given barcode is not in manual mode, When backend emits barcode message with valid %s, Then ws client updates correct barcode in store",
      async (barcodeType, old_barcode, valid_barcode, beta2Mode) => {
        const message = {
          [barcodeType]: valid_barcode,
        };
        await store.commit("settings/setBeta2Mode", beta2Mode);
        await store.commit("flask/setBarcodeManualMode", false);
        await store.commit("playback/setBarcode", {
          type: barcodeType,
          new_value: old_barcode,
          is_valid: true,
        });

        // confirm precondition
        expect(store.state.playback.barcodes[barcodeType].value).toBe(old_barcode);

        await new Promise((resolve) => {
          socket_server_side.emit("barcode", JSON.stringify(message), (ack) => {
            resolve(ack);
          });
        });

        const stim_config_state = store.state.stimulation.stimStatus === STIM_STATUS.NO_PROTOCOLS_ASSIGNED;

        expect(store.state.playback.barcodes[barcodeType].value).toBe(valid_barcode);
        expect(store.state.playback.barcodes[barcodeType].valid).toBe(true);
        expect(stim_config_state).toBe(true);
      }
    );
    test.each([
      ["plateBarcode", valid_plateBarcode_old],
      ["stimBarcode", valid_stimBarcode_old],
    ])(
      "Given barcode is in manual mode, When backend emits barcode message with valid %s, Then ws client does not set new barcode in store",
      async (barcodeType, valid_barcode) => {
        const message = {
          barcodeType: valid_barcode,
        };

        store.commit("flask/setBarcodeManualMode", true);

        // confirm precondition
        expect(store.state.playback.barcodes[barcodeType].value).toBeNull();

        await new Promise((resolve) => {
          socket_server_side.emit("barcode", JSON.stringify(message), (ack) => {
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
      async (error_type) => {
        expect(store.state.settings.shutdownErrorStatus).toBe("");

        const latest_compatible_sw_version =
          error_type === "FirmwareAndSoftwareNotCompatibleError" ? "1.2.3" : null;

        await new Promise((resolve) => {
          socket_server_side.emit(
            "error",
            JSON.stringify({ error_type, latest_compatible_sw_version }),
            (ack) => {
              resolve(ack);
            }
          );
        });

        const additional_text = latest_compatible_sw_version
          ? ". Please download the installer for the correct version here:"
          : ". Mantarray Controller is about to shutdown.";

        expect(store.state.settings.shutdownErrorStatus).toBe(ERRORS[error_type] + additional_text);
      }
    );
  });

  // TODO move these to another test file
  describe("Given current status is LIVE_VIEW_ACTIVE", () => {
    let mocked_axios;
    let context = null;

    beforeEach(async () => {
      mocked_axios = new MockAxiosAdapter(axios);

      store.commit("data/set_plate_waveforms", ar);
      context = await store.dispatch("flask/get_flask_action_context");

      store.commit("flask/setStatusUuid", STATUS.MESSAGE.LIVE_VIEW_ACTIVE);
    });

    test("When xTimeIndex is set to a specific value in Vuex, Then the /system_status route is called with Axios with the xTimeIndex as a parameter", async () => {
      const expected_idx = 9876;
      store.commit("playback/set_xTimeIndex", expected_idx);
      mocked_axios.onGet(system_status_regexp).reply(200, nr);

      const bound_ping_system_status = ping_system_status.bind(context);
      await bound_ping_system_status();
      expect(mocked_axios.history.get).toHaveLength(1);
      expect(mocked_axios.history.get[0].url).toMatch(new RegExp("http://localhost:4567/system_status?"));
      expect(mocked_axios.history.get[0].params.currently_displayed_time_index).toEqual(expected_idx);
    });

    test("Given /system_status is mocked to return 200 (and some dummy response) and and /start_recording is mocked to return an HTTP error, When start_recording is dispatched, Then both intervals are cleared in Vuex (status pinging, and playback progression)", async () => {
      mocked_axios
        .onGet(system_status_regexp)
        .reply(200, {
          ui_status_code: STATUS.MESSAGE.CALIBRATION_NEEDED,
          in_simulation_mode: true,
        })
        .onGet("/start_recording")
        .reply(405);

      await store.dispatch("flask/start_status_pinging");
      await store.dispatch("playback/start_playback_progression");

      // confirm pre-conditions
      expect(store.state.flask.statusPingIntervald).not.toBeNull();
      expect(store.state.playback.playback_progression_interval_id).not.toBeNull();

      await store.dispatch("playback/start_recording");

      expect(store.state.flask.statusUuid).toStrictEqual(STATUS.MESSAGE.ERROR);
      expect(store.state.flask.statusPingIntervald).toBeNull();
      expect(store.state.playback.playback_progression_interval_id).toBeNull();
    });
  });
});
