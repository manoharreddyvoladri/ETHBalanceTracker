const express = require('express');
const router = express.Router();
const Deposit = require('../models/Deposit');

router.post('/', async (req, res) => {
  const deposit = new Deposit(req.body);
  try {
    const savedDeposit = await deposit.save();
    res.status(201).json(savedDeposit);
  } catch (error) {
    res.status(400).json({ message: error.message });
  }
});

router.get('/', async (req, res) => {
  try {
    const deposits = await Deposit.find().sort({ blockTimestamp: -1 }).limit(100);
    res.json(deposits);
  } catch (error) {
    res.status(500).json({ message: error.message });
  }
});

module.exports = router;