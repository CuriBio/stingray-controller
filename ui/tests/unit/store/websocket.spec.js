import { socket as socketClientSide } from "@/store/plugins/websocket";
import Vuex from "vuex";
import { createLocalVue } from "@vue/test-utils";

const http = require("http");
const WebSocketServer = require("websocket").server;

describe("store/data", () => {
  const localVue = createLocalVue();
  localVue.use(Vuex);
  let NuxtStore;
  let store;

  beforeAll(async () => {
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
    // event handlers persist through tests, so clear them all before any tests in this file run
    // socketClientSide.close();
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });

  //   afterEach(() => {
  //     // event handlers persist through tests, so clear them all after each test
  //     socketClientSide.close();
  //   });

  describe("websocket", () => {
    let httpServer;
    let wsServer;
    let socketServerSide;

    beforeAll((done) => {
      httpServer = http.createServer().listen(4567); // TODO use constant here
      wsServer = new WebSocketServer({
        httpServer,
        autoAcceptConnections: false,
      });
      // wait for connection
      wsServer.on("request", (request) => {
        // request.on("message", message => {
        //   console.log(`received from a client: ${message}`);
        // });
        request.socket.emit(
          "onmessage",
          JSON.stringify({
            communication_type: "user_input_needed",
          })
        );

        // socketServerSide = request.socket;
        // socketServerSide.emit(
        //   "message",
        //   JSON.stringify({
        //     communication_type: "user_input_needed"
        //   })
        // );
        done();
      });
      //   httpServer = http.createServer().listen(4567); // TODO use constant here
      //   wsServer = io_server(httpServer);
      // wait for connection
      //   wsServer.on("connect", socket => {
      //     console.log("LUC: ", socket);
      //     socketServerSide = socket;
      //     done();
      //   });
    });

    afterAll(() => {
      if (socketServerSide.connected) {
        socketServerSide.disconnect();
      }

      wsServer.close();
      httpServer.close();
      socketClientSide.close();
    });

    test("When backend emits promptUserInput message with customerCreds as input type, Then ws client sets correct flag in store", async () => {
      const message = {
        communication_type: "user_input_needed",
      };

      // confirm precondition
      expect(store.state.settings.userCredInputNeeded).toBe(true);

      //   await new Promise(resolve => {
      //     console.log(socketServerSide);
      //     socketServerSide.emit(JSON.stringify({ message }));
      //     resolve();
      //   });

      //   expect(store.state.settings.userCredInputNeeded).toBe(true);
    });
  });
});
