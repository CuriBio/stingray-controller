export default {
  async updateSettings() {
    const { activeUserIndex, userAccounts } = this.state.settings;
    const { customerId, userPassword, userName } = userAccounts[activeUserIndex];
    const params = {
      command: "update_user_settings",
      customer_id: customerId,
      user_name: userName,
      user_password: userPassword,
    };

    this.state.system.socket.send(JSON.stringify(params));
    // TODO remove response here and update from WS response message
    return 200;
  },
};
