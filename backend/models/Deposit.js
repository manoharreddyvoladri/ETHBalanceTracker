const mongoose = require('mongoose');

const DepositSchema = new mongoose.Schema({
  blockNumber: {
    type: Number,
    required: true
  },
  blockTimestamp: {
    type: Number,
    required: true
  },
  amount: {
    type: Number,
    required: true
  },
  pubkey: {
    type: String,
    required: true
  }
}, { timestamps: true });

module.exports = mongoose.model('Deposit', DepositSchema);