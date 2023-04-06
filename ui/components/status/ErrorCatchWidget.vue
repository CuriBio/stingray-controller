<template>
  <div class="div__status-error-catch-background">
    <div class="div__status-error-catch-title-label">An&nbsp;<wbr />error&nbsp;<wbr />occurred.</div>
    <p class="p__status-error-catch-alert-txt">{{ systemErrorMessage }}</p>
    <p class="p__status-error-catch-alert-txt">{{ `Error Code: ${systemErrorCode}` }}</p>
    <textarea
      v-if="installerLink"
      class="textarea__installer_filepath"
      name="installer_link"
      rows="2"
      cols="75"
      spellcheck="false"
      :value.prop="installerLink"
      :disabled="true"
    />
    <p class="p__status-error-catch-alert-txt">
      Please send the folder shown below to
      <a id="errorContact" href="mailto:support@curibio.com ? subject = Stingray Error log"
        >support@curibio.com</a
      >
    </p>
    <textarea
      class="textarea__installer_filepath"
      name="error_file"
      rows="2"
      cols="50"
      spellcheck="false"
      :value.prop="logPath"
      :disabled="true"
    />
    <p class="p__status-error-catch-alert-txt" style="margin-bottom: 15px">
      Please turn the instrument off, unplug from the PC,<br />
      and then wait 10 seconds before attempting to use again.
    </p>
    <div class="div__error-button">
      <ButtonWidget
        :buttonWidgetWidth="450"
        :buttonWidgetHeight="50"
        :buttonWidgetTop="0"
        :buttonWidgetLeft="0"
        :buttonNames="['Okay']"
        :enabledColor="'#B7B7B7'"
        :hoverColor="['#FFFFFF']"
        @btn-click="processOk"
      />
    </div>
  </div>
</template>

<script>
import ButtonWidget from "@/components/basic-widgets/ButtonWidget.vue";
import { mapState } from "vuex";

export default {
  components: {
    ButtonWidget,
  },
  computed: {
    ...mapState("system", ["systemErrorCode", "systemErrorMessage", "installerLink"]),
    ...mapState("settings", ["logPath"]),
  },
  methods: {
    processOk: function () {
      this.$emit("ok-clicked");
    },
  },
};
</script>
<style>
a:link {
  color: #b7b7b7;
  background-color: transparent;
  text-decoration: none;
}
a:hover {
  color: #ffffff;
  background-color: transparent;
  text-decoration: none;
}
.div__status-error-catch-background {
  pointer-events: all;
  transform: rotate(0deg);
  position: absolute;
  background: rgb(17, 17, 17);
  width: 450px;
  top: 0px;
  left: 0px;
  visibility: visible;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.div__status-error-catch-title-label {
  pointer-events: all;
  line-height: 1.5;
  transform: rotate(0deg);
  overflow: hidden;
  position: relative;
  width: 450px;
  height: 30px;
  margin: 11px 0;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 17px;
  color: rgb(255, 255, 255);
  text-align: center;
}
.p__status-error-catch-alert-txt {
  transform: rotate(0deg);
  padding: 0px;
  margin: 5px 0;
  overflow-wrap: break-word;
  color: rgb(183, 183, 183);
  font-family: Muli;
  position: relative;
  width: 450px;
  overflow: hidden;
  visibility: visible;
  user-select: none;
  text-align: center;
  font-size: 15px;
  letter-spacing: normal;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  pointer-events: all;
}
.div__error-button {
  position: relative;
  margin-right: 100%;
}
.textarea__installer_filepath {
  /* line-height: 1.2; */
  transform: rotate(0deg);
  margin: 8px 0;
  word-break: break-all;
  outline: none;
  color: rgb(183, 183, 183);
  font-family: Courier New;
  position: relative;
  background: rgb(17, 17, 17);
  border: 2px solid rgb(17, 17, 17);
  border-radius: 0px;
  box-shadow: none;
  overflow: hidden;
  visibility: visible;
  width: 350px;
  user-select: none;
  vertical-align: top;
  text-align: center;
  font-size: 15px;
  letter-spacing: normal;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  resize: none;
  pointer-events: all;
}
</style>
