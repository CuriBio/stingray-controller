<template>
  <div>
    <div class="div__settingsform-controls">
      <span class="span__settingsform-title">User Settings</span>
      <canvas class="canvas__settingsform-separator" />
      <div class="div__settingsform-editor-input">
        <InputWidget
          :titleLabel="'Select Customer ID'"
          :placeholder="'ba86b8f0-6fdf-4944-87a0-8a491a19490e'"
          :invalidText="errorText.customerId"
          :inputWidth="400"
          :initialValue="userDetails.customerId"
          :containerBackgroundColor="'rgba(0, 0, 0)'"
          :inputBackgroundColor="'#1c1c1c'"
          :domIdSuffix="'customer-id'"
          @update:value="onUpdateInput($event, 'customerId')"
        />
      </div>
      <div class="div__settingsform-editor-input">
        <InputDropDown
          :titleLabel="'Select User'"
          :placeholder="'user account 1'"
          :invalidText="errorText.username"
          :inputWidth="400"
          :value="userDetails.username"
          :optionsText="storedUsernames"
          :optionsId="'user-account-'"
          @update:value="onUpdateInput($event, 'username')"
        />
      </div>
      <div class="div__settingsform-editor-input">
        <InputWidget
          :titleLabel="'Enter Password'"
          :placeholder="'****'"
          :invalidText="errorText.password"
          :type="'password'"
          :spellcheck="false"
          :initialValue="userDetails.password"
          :containerBackgroundColor="'rgba(0, 0, 0)'"
          :inputBackgroundColor="'#1c1c1c'"
          :inputWidth="400"
          :domIdSuffix="'passkey-id'"
          @update:value="onUpdateInput($event, 'password')"
        />
      </div>
      <canvas class="canvas__settingsform-separator" />
    </div>
    <div class="div__settings-tool-tip-cancel-btn" @click="cancelChanges">
      <span class="span__settings-tool-tip-btn-txt">Close</span>
    </div>
    <div
      class="div__settings-tool-tip-login-btn"
      :class="`div__settings-tool-tip-login-btn-${isLoginEnabled ? 'enable' : 'disable'}`"
    >
      <span
        class="span__settings-tool-tip-btn-txt"
        :class="`span__settings-tool-tip-login-btn-txt-${isLoginEnabled ? 'enable' : 'disable'}`"
        @click="loginUser"
        >Login</span
      >
    </div>
  </div>
</template>
<script>
import Vue from "vue";
import { mapState } from "vuex";
import BootstrapVue from "bootstrap-vue";
import { BButton } from "bootstrap-vue";
import { BModal } from "bootstrap-vue";
import { BFormInput } from "bootstrap-vue";
import InputDropDown from "@/components/basic-widgets/InputDropDown.vue";
import InputWidget from "@/components/basic-widgets/InputWidget.vue";

Vue.use(BootstrapVue);
Vue.component("BButton", BButton);
Vue.component("BModal", BModal);
Vue.component("BFormInput", BFormInput);

export default {
  name: "SettingsForm",
  components: {
    InputDropDown,
    InputWidget,
  },
  data() {
    return {
      disableSettings: true,
      invalidCredsFound: false,
      userDetails: {
        customerId: "",
        password: "",
        username: "",
      },
    };
  },
  computed: {
    ...mapState("settings", ["userAccount", "storedCustomerId", "storedUsernames"]),
    ...mapState("system", ["loginAttemptStatus"]),
    isLoginEnabled: function () {
      return !Object.values(this.errorText).some((val) => val !== "");
    },
    errorText: function () {
      return this.invalidCredsFound
        ? {
            customerId: "Invalid Customer ID, Username, or Password",
            username: "Invalid Customer ID, Username, or Password",
            password: "Invalid Customer ID, Username, or Password",
          }
        : {
            customerId: this.userDetails.customerId && this.userDetails.customerId !== "" ? "" : "Required",
            username: this.userDetails.username && this.userDetails.username !== "" ? "" : "Required",
            password: this.userDetails.password && this.userDetails.password !== "" ? "" : "Required",
          };
    },
    isUserLoggedIn: function () {
      return this.userAccount.username && this.userAccount.username !== "";
    },
  },
  watch: {
    loginAttemptStatus: function (status) {
      if (status) {
        this.$store.commit("settings/setUserAccount", this.userDetails);
        this.$emit("close-modal", true);
      } else if (status === false) {
        // need to check explicitly for false since null is also used
        // if login fails, prompt user to re-enter their credentials
        this.invalidCredsFound = true;
      }
    },
    storedCustomerId: function () {
      this.userDetails.customerId = this.storedCustomerId;
    },
  },
  methods: {
    async loginUser() {
      this.$store.commit("system/setLoginAttemptStatus", null); // set this back to null to indicate that the result is pending
      this.$store.dispatch("settings/sendLoginCommand", this.userDetails);
    },
    onUpdateInput: function (newValue, field) {
      this.invalidCredsFound = false;
      this.userDetails = { ...this.userDetails, [field]: newValue };
    },
    cancelChanges() {
      // reset inputs back to stored state
      this.userDetails = { ...this.userAccount };

      this.$emit("close-modal", false);
    },

    handleToggleState(state, label) {
      this[label] = state;
    },
  },
};
</script>
<style scoped>
.div__settingsform-controls {
  top: 0px;
  left: 0px;
  background-color: rgba(0, 0, 0);
  width: 700px;
  height: 488px;
  position: absolute;
  overflow: hidden;
  pointer-events: none;
  z-index: 2;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.span__settingsform-title {
  pointer-events: all;
  line-height: 100%;
  transform: rotate(0deg);
  overflow: hidden;
  position: relative;
  width: 700px;
  height: 34px;
  margin-top: 13px;
  left: 0px;
  padding: 5px;
  visibility: visible;
  user-select: none;
  font-family: Muli;
  font-weight: normal;
  font-style: normal;
  text-decoration: none;
  font-size: 23px;
  color: rgb(255, 255, 255);
  text-align: center;
  z-index: 3;
  background-color: rgba(0, 0, 0);
}

.div__settingsform-editor-input {
  pointer-events: all;
  white-space: nowrap;
  line-height: 100%;
  transform: rotate(0deg);
  position: relative;
  width: 400px;
  height: 100px;
  padding: 0px;
  visibility: visible;
}

.canvas__settingsform-separator {
  transform: rotate(0deg);
  pointer-events: all;
  position: relative;
  width: 510px;
  height: 1px;
  background-color: #878d99;
  opacity: 0.5;
  margin: 12px 0;
}

.div__settings-tool-tip-cancel-btn {
  pointer-events: all;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 180px;
  height: 55px;
  top: 411px;
  left: 365px;
  visibility: visible;
  z-index: 55;
  background-color: rgb(183, 183, 183);
}
.div__settings-tool-tip-login-btn {
  pointer-events: all;
  transform: rotate(0deg);
  overflow: hidden;
  position: absolute;
  width: 180px;
  height: 55px;
  top: 411px;
  left: 164px;
  visibility: visible;
  z-index: 55;
}
.div__settings-tool-tip-login-btn-enable {
  background-color: rgb(183, 183, 183);
}

.div__settings-tool-tip-login-btn-disable {
  background-color: #b7b7b7c9;
}

.div__settings-tool-tip-login-btn-enable:hover {
  background-color: #19ac8a;
  cursor: pointer;
}

.div__settings-tool-tip-cancel-btn:hover {
  background-color: #b7b7b7c9;
  cursor: pointer;
}

.span__settings-tool-tip-btn-txt {
  padding-left: 5px;
  padding-right: 5px;
  overflow: hidden;
  white-space: nowrap;
  text-align: center;
  font-weight: normal;
  transform: translateZ(0px);
  position: absolute;
  width: 170px;
  height: 45px;
  line-height: 47px;
  top: 5px;
  left: 5px;
  user-select: none;
  font-family: Muli;
  font-style: normal;
  text-decoration: none;
  font-size: 16px;
  color: rgb(0, 0, 0);
  z-index: 55;
}

.span__settings-tool-tip-login-btn-txt-disable {
  color: #6e6f72;
}

.span__settings-tool-tip-login-btn-txt-enable {
  color: rgb(0, 0, 0);
}
</style>
