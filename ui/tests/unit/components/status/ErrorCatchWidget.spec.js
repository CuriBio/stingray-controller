import { mount } from "@vue/test-utils";
import ComponentToTest from "@/components/status/ErrorCatchWidget.vue";
import { ErrorCatchWidget as DistComponentToTest } from "@/dist/mantarray.common";
import { shallowMount } from "@vue/test-utils";

import Vuex from "vuex";
import { createLocalVue } from "@vue/test-utils";

let wrapper = null;

const localVue = createLocalVue();
localVue.use(Vuex);

let NuxtStore;
let store;

describe("ErrorCatchWidget.vue", () => {
  beforeAll(async () => {
    // note the store will mutate across tests, so make sure to re-create it in beforeEach
    const storePath = `${process.env.buildDir}/store.js`;
    NuxtStore = await import(storePath);
  });

  beforeEach(async () => {
    store = await NuxtStore.createStore();
  });

  afterEach(() => wrapper.destroy());

  test("When mounting ErrorCatchWidget from the build dist file, Then it loads successfully and the background black box is displayed", () => {
    const propsData = {
      logFilepath: "C:\\ ",
    };
    wrapper = shallowMount(DistComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetBackgroundDiv = wrapper.find(".div__status-error-catch-background");
    expect(targetBackgroundDiv.isVisible()).toBe(true);
  });
  test("Given that ErrorCatchWidget has a props having error file name and error message, When the lifecyle hook mounted is created, Then title, alert text, contact e-mail and error file name is rendered properly", async () => {
    const propsData = {
      logFilepath: "C:\testFileLog.txt",
      shutdownErrorMessage: "Mantarray software is about to shut down.",
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetTitleDiv = wrapper.find(".divStatus-error-catch-title-label");
    expect(targetTitleDiv.text()).toStrictEqual("An error occurred.");
    const targetAlertDiv = wrapper.find(".divStatus-error-catch-alert-txt");
    const targetAlertDivP = targetAlertDiv.findAll("p");
    expect(targetAlertDivP.at(0).text()).toStrictEqual("Mantarray software is about to shut down.");

    const targetEmailDivP = wrapper.find(".divStatus-email-txt").findAll("p");
    expect(targetEmailDivP.at(0)).toMatchInlineSnapshot(`
      <p>
        Please send the folder shown below to
        <a id="errorContact" href="mailto:support@curibio.com ? subject = Mantarray Error log">support@curibio.com</a>
      </p>
    `);

    await wrapper.vm.$nextTick(); // wait for update
    const targetTextArea = wrapper.find(".textarea__error-file-path");
    expect(targetTextArea.element.value).toStrictEqual("C:\testFileLog.txt");
  });
  test("Given that ErrorCatchWidget has a props having logFilepath is small, When mounting the component with short logFilepath, Then the text area rows attribute is modified to suite the length of props logFilepath intially, at run time based on new logFilepath then the rows attribute of textarea is updated", async () => {
    const propsData = {
      logFilepath: "C:\testFileLog.txt",
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    await wrapper.vm.$nextTick(); // wait for update
    const targetTextArea = wrapper.find(".textarea__error-file-path");
    expect(targetTextArea.attributes("rows")).toBe("1");
    await wrapper.setProps({
      logFilepath:
        "C:UsersEliCuriBioAppDataRoamingStringrayControllerlogsFlaskmantarray-2020-10-21-185640.txt",
    });
    expect(targetTextArea.attributes("rows")).toBe("3");
  });
  test("Given that ErrorCatchWidget has a props having logFilepath is small, When mounting the component with short logFilepath, Then the height attribute of the status-error-catch-background, textarea__error-file-path and the top attribute of errorCatchButton is updated based on the length prop logFilepath", async () => {
    const propsData = {
      logFilepath: "C:\testFileLog.txt",
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    const targetBackgroundDiv = wrapper.find(".div__status-error-catch-background");
    expect(targetBackgroundDiv.attributes().style).toBe("height: 262px;");
    const targetTextArea = wrapper.find(".textarea__error-file-path");
    expect(targetTextArea.attributes().style).toBe("height: 37px; top: 145px;");
    const targetErrorButton = wrapper.find(".div__error-button");
    expect(targetErrorButton.attributes().style).toBe("top: 262px; left: 0px; position: absolute;");
    /* A run time update of prop occured below then observe that height value and top is updated */
    await wrapper.setProps({
      logFilepath: "C:UsersMantarrayAppDataRoamingStringrayControllerlogsFlask",
    });
    expect(targetBackgroundDiv.attributes().style).toBe("height: 274px;");
    expect(targetTextArea.attributes().style).toBe("height: 49px; top: 145px;");
    expect(targetErrorButton.attributes().style).toBe("top: 274px; left: 0px; position: absolute;");
  });
  test("Given that ErrorCatchWidget is mounted, When the ErrorCatchWidget is visible, Then click on 'Okay' results in an event 'ok-clicked' to be emitted", async () => {
    const propsData = {
      logFilepath: "C:\testFileLog.txt",
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });

    const okayBtn = wrapper.find(".span__button-label");
    await okayBtn.trigger("click");
    await wrapper.vm.$nextTick();
    const okayBtnEvents = wrapper.emitted("ok-clicked");
    expect(okayBtnEvents).toHaveLength(1);
    expect(okayBtnEvents[0]).toStrictEqual([]);
  });
});
