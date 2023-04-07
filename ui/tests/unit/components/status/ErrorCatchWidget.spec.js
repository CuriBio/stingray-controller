import { mount } from "@vue/test-utils";
import ComponentToTest from "@/components/status/ErrorCatchWidget.vue";
import { ErrorCatchWidget as DistComponentToTest } from "@/dist/stingray.common";
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
    };
    wrapper = mount(ComponentToTest, {
      propsData,
      store,
      localVue,
    });
    await store.commit("system/setSystemErrorMessage", "Stingray Controller is about to shut down.");
    const targetTitleDiv = wrapper.find(".div__status-error-catch-title-label");
    expect(targetTitleDiv.text()).toStrictEqual("An error occurred.");
    const targetAlertP = wrapper.findAll(".p__status-error-catch-alert-txt");
    expect(targetAlertP.at(0).text()).toStrictEqual("Stingray Controller is about to shut down.");

    expect(targetAlertP.at(2)).toMatchInlineSnapshot(`
      <p class="p__status-error-catch-alert-txt">
        Please send the folder shown below to
        <a id="errorContact" href="mailto:support@curibio.com ? subject = Stingray Error log">support@curibio.com</a>
      </p>
    `);

    await wrapper.vm.$nextTick(); // wait for update
    const targetTextArea = wrapper.find(".textarea__installer_filepath");
    expect(targetTextArea.element.value).toStrictEqual("C:\testFileLog.txt");
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
