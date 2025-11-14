# CrapsSim API — Seed Sanity Verification Run

### 1. Start Session
POST /session/start
Request:
```json
{
  "profile": "test-profile",
  "seed": 12345
}
```
Response:
```json
{
  "session_id": "3bdec67c",
  "snapshot": {
    "bankroll_after": "1000.00",
    "capabilities": {
      "bets": {
        "buy": [
          "buy_4",
          "buy_5",
          "buy_6",
          "buy_8",
          "buy_9",
          "buy_10"
        ],
        "field": {
          "pays": {
            "12": "double",
            "2": "double"
          }
        },
        "hardways": {
          "break_on": "seven_or_easy"
        },
        "lay": [
          "lay_4",
          "lay_5",
          "lay_6",
          "lay_8",
          "lay_9",
          "lay_10"
        ],
        "line": [
          "pass_line",
          "dont_pass",
          "come",
          "dont_come",
          "odds",
          "put"
        ],
        "place": [
          "place_4",
          "place_5",
          "place_6",
          "place_8",
          "place_9",
          "place_10"
        ],
        "props": [
          "any7",
          "c&e",
          "horn",
          "world"
        ]
      },
      "increments": {
        "place": {
          "10": 5,
          "4": 5,
          "5": 5,
          "6": 6,
          "8": 6,
          "9": 5
        }
      },
      "odds_limits": {
        "max_x": 20,
        "policy": "3-4-5"
      },
      "schema_version": 1,
      "vig": {
        "buy": {
          "floor": 0.0,
          "paid_on_win": false,
          "rate_bips": 500,
          "rounding": "nearest_dollar"
        },
        "lay": {
          "floor": 0.0,
          "paid_on_win": false,
          "rate_bips": 500,
          "rounding": "nearest_dollar"
        }
      },
      "why_unsupported": {
        "fire": "not implemented in vanilla",
        "small_tall_all": "not implemented in vanilla"
      },
      "working_flags": {
        "comeout_odds_work": false,
        "place_work_comeout": false
      }
    },
    "dice": null,
    "events": [],
    "hand_id": 1,
    "identity": {
      "capabilities_schema_version": 1,
      "engine_api_version": "0.4.0-api-p4",
      "engine_version": "0.4.0-api-p4",
      "seed": 12345,
      "table_profile": "test-profile"
    },
    "point": null,
    "puck": "OFF",
    "roll_seq": 0,
    "session_id": "3bdec67c"
  }
}
```

### 2. Place Pass Line
POST /session/action
Request:
```json
{
  "action": "place",
  "bets": [
    {
      "amount": 10,
      "type": "pass_line"
    }
  ],
  "session_id": "3bdec67c"
}
```
Response:
```json
{
  "results": [
    {
      "applied": true,
      "args": {
        "amount": 10.0
      },
      "bankroll_delta": 0.0,
      "cash_required": 10.0,
      "note": "validated (legal, stub execution)",
      "verb": "pass_line"
    }
  ],
  "snapshot": {
    "bankroll_after": 990.0,
    "identity": {
      "capabilities_schema_version": 1,
      "engine_api_version": "0.4.0-api-p4"
    },
    "point": null,
    "puck": "OFF",
    "session_id": "3bdec67c"
  }
}
```

### 3. Roll 1
POST /session/roll
Request:
```json
{
  "session_id": "3bdec67c"
}
```
Response:
```json
{
  "snapshot": {
    "bankroll_after": "1000.00",
    "dice": [
      5,
      4
    ],
    "events": [
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {},
        "hand_id": 1,
        "id": "da04eebb7a61",
        "roll_seq": 1,
        "ts": "2025-11-14T01:04:13Z",
        "type": "hand_started"
      },
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "mode": "auto"
        },
        "hand_id": 1,
        "id": "0cfd68a280a3",
        "roll_seq": 1,
        "ts": "2025-11-14T01:04:13Z",
        "type": "roll_started"
      },
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "dice": [
            5,
            4
          ]
        },
        "hand_id": 1,
        "id": "922e6a2b96fb",
        "roll_seq": 1,
        "ts": "2025-11-14T01:04:13Z",
        "type": "roll_completed"
      },
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "point": 9
        },
        "hand_id": 1,
        "id": "d3c41f5402bb",
        "roll_seq": 1,
        "ts": "2025-11-14T01:04:13Z",
        "type": "point_set"
      }
    ],
    "hand_id": 1,
    "identity": {
      "capabilities_schema_version": 1,
      "engine_api_version": "0.4.0-api-p4"
    },
    "point": 9,
    "puck": "ON",
    "roll_seq": 1,
    "session_id": "3bdec67c"
  }
}
```

### 4. Roll 2
POST /session/roll
Request:
```json
{
  "session_id": "3bdec67c"
}
```
Response:
```json
{
  "snapshot": {
    "bankroll_after": "1000.00",
    "dice": [
      5,
      4
    ],
    "events": [
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "mode": "auto"
        },
        "hand_id": 1,
        "id": "4ea0f956f2ee",
        "roll_seq": 2,
        "ts": "2025-11-14T01:04:13Z",
        "type": "roll_started"
      },
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "dice": [
            5,
            4
          ]
        },
        "hand_id": 1,
        "id": "9a509f77bba5",
        "roll_seq": 2,
        "ts": "2025-11-14T01:04:13Z",
        "type": "roll_completed"
      },
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "point": 9
        },
        "hand_id": 1,
        "id": "d2341dce1930",
        "roll_seq": 2,
        "ts": "2025-11-14T01:04:13Z",
        "type": "point_made"
      },
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "end_reason": "point_made"
        },
        "hand_id": 1,
        "id": "9443256c5eba",
        "roll_seq": 2,
        "ts": "2025-11-14T01:04:13Z",
        "type": "hand_ended"
      }
    ],
    "hand_id": 2,
    "identity": {
      "capabilities_schema_version": 1,
      "engine_api_version": "0.4.0-api-p4"
    },
    "point": null,
    "puck": "OFF",
    "roll_seq": 2,
    "session_id": "3bdec67c"
  }
}
```

### 5. Roll 3
POST /session/roll
Request:
```json
{
  "session_id": "3bdec67c"
}
```
Response:
```json
{
  "snapshot": {
    "bankroll_after": "1000.00",
    "dice": [
      5,
      4
    ],
    "events": [
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "mode": "auto"
        },
        "hand_id": 2,
        "id": "62b79e37c8a8",
        "roll_seq": 3,
        "ts": "2025-11-14T01:04:13Z",
        "type": "roll_started"
      },
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "dice": [
            5,
            4
          ]
        },
        "hand_id": 2,
        "id": "1cca54cfef37",
        "roll_seq": 3,
        "ts": "2025-11-14T01:04:13Z",
        "type": "roll_completed"
      },
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "point": 9
        },
        "hand_id": 2,
        "id": "803a37dd3276",
        "roll_seq": 3,
        "ts": "2025-11-14T01:04:13Z",
        "type": "point_set"
      }
    ],
    "hand_id": 2,
    "identity": {
      "capabilities_schema_version": 1,
      "engine_api_version": "0.4.0-api-p4"
    },
    "point": 9,
    "puck": "ON",
    "roll_seq": 3,
    "session_id": "3bdec67c"
  }
}
```

### 6. Place 6
POST /session/action
Request:
```json
{
  "action": "place",
  "bets": [
    {
      "amount": 12,
      "type": "place_6"
    }
  ],
  "session_id": "3bdec67c"
}
```
Response:
```json
{
  "results": [
    {
      "applied": true,
      "args": {
        "amount": 12.0,
        "box": 6
      },
      "bankroll_delta": 0.0,
      "cash_required": 12.0,
      "note": "validated (legal, stub execution)",
      "verb": "place"
    }
  ],
  "snapshot": {
    "bankroll_after": 978.0,
    "identity": {
      "capabilities_schema_version": 1,
      "engine_api_version": "0.4.0-api-p4"
    },
    "point": 9,
    "puck": "ON",
    "session_id": "3bdec67c"
  }
}
```

### 7. Roll 4
POST /session/roll
Request:
```json
{
  "session_id": "3bdec67c"
}
```
Response:
```json
{
  "snapshot": {
    "bankroll_after": "1000.00",
    "dice": [
      5,
      4
    ],
    "events": [
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "mode": "auto"
        },
        "hand_id": 2,
        "id": "69e82f0cb135",
        "roll_seq": 4,
        "ts": "2025-11-14T01:04:13Z",
        "type": "roll_started"
      },
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "dice": [
            5,
            4
          ]
        },
        "hand_id": 2,
        "id": "58246ca357b1",
        "roll_seq": 4,
        "ts": "2025-11-14T01:04:13Z",
        "type": "roll_completed"
      },
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "point": 9
        },
        "hand_id": 2,
        "id": "e766d6716970",
        "roll_seq": 4,
        "ts": "2025-11-14T01:04:13Z",
        "type": "point_made"
      },
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "end_reason": "point_made"
        },
        "hand_id": 2,
        "id": "a227deef03f6",
        "roll_seq": 4,
        "ts": "2025-11-14T01:04:13Z",
        "type": "hand_ended"
      }
    ],
    "hand_id": 3,
    "identity": {
      "capabilities_schema_version": 1,
      "engine_api_version": "0.4.0-api-p4"
    },
    "point": null,
    "puck": "OFF",
    "roll_seq": 4,
    "session_id": "3bdec67c"
  }
}
```

### 8. Roll 5
POST /session/roll
Request:
```json
{
  "session_id": "3bdec67c"
}
```
Response:
```json
{
  "snapshot": {
    "bankroll_after": "1000.00",
    "dice": [
      5,
      4
    ],
    "events": [
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "mode": "auto"
        },
        "hand_id": 3,
        "id": "539ce742d8de",
        "roll_seq": 5,
        "ts": "2025-11-14T01:04:13Z",
        "type": "roll_started"
      },
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "dice": [
            5,
            4
          ]
        },
        "hand_id": 3,
        "id": "274593d1943f",
        "roll_seq": 5,
        "ts": "2025-11-14T01:04:13Z",
        "type": "roll_completed"
      },
      {
        "bankroll_after": "1000.00",
        "bankroll_before": "1000.00",
        "data": {
          "point": 9
        },
        "hand_id": 3,
        "id": "f4cd0a181919",
        "roll_seq": 5,
        "ts": "2025-11-14T01:04:13Z",
        "type": "point_set"
      }
    ],
    "hand_id": 3,
    "identity": {
      "capabilities_schema_version": 1,
      "engine_api_version": "0.4.0-api-p4"
    },
    "point": 9,
    "puck": "ON",
    "roll_seq": 5,
    "session_id": "3bdec67c"
  }
}
```
