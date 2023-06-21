# Client Service: 

URL:http://localhost:5501/

  /client [POST]:
  
    Payload:
      {
        "username": "Eric",
        "password": "123",
        "role": 0
      }
    
    Response:
      {
        "id": 4
      }
      
  /client [GET]:
  
    Response:
    [
        {
            "id": 1,
            "username": "Kelly",
            "password": "$2b$12$EFd9rmfU4rKTxoMEyI1Gz.Fa1svme/S9c01x0Em1xzuKS0IXg4QbS",
            "role": 0
        },
        {
            "id": 2,
            "username": "Dion",
            "password": "$2b$12$znyv5qAJk3Qr8wwPhhzgSOUiaemaOUVP3ZKGqaxRRzFpGBR9yw4PS",
            "role": 0
        },
        {
            "id": 3,
            "username": "Eric",
            "password": "$2b$12$im.oHxd8m7DkgiXz9jQpN.ptsVMKsjf8iuxByhgjatc8XGVqnD6X2",
            "role": 0
        }
    ]
    
  /client/id [PUT]:
  
    Payload:
    {
      "username": "Jen", -> Username gaboleh sama
      "password": "123",
      "role": 0
    }
    
    Response:
    {
      "event": "updated_client",
      "id": 4,
      "username": "Jeni",
      "password": "123",
      "role": 0
    }
  
  /client/id [GET]:
  
    Response:
    {
      "id": 4,
      "username": "Jeni",
      "password": "$2b$12$XzHBQnEqXUa/7tuil.ne7.7GB/aVO5IQoINphXebv0Aotwc/oaNoG",
      "role": 0
    }


# Staff Service: 

URL: http://localhost:5503/

  /staff [POST]:
  
    Payload:
      {
        "username": "Eric",
        "password": "123",
        "role": 0
      }
    
    Response:
      {
        "id": 4
      }
      
  /staff [GET]:
  
    Response:
      [
          {
              "id": 1,
              "username": "Wendy",
              "password": "$2b$12$UacGq1taqEieY3SdSIDzOe3c3tUBpYNdYQl3iVLHfbOGP/BT4GN5m",
              "role": 1
          }
      ]
    
  /staff/id [PUT]:
  
    Payload:
      {
        "username": "Wendy", -> Username gaboleh sama
        "password": "123",
        "role": 1
      }
    
    Response:
      {
        "event": "updated_staff",
        "id": 1,
        "username": "WendySan",
        "password": "123",
        "role": 1
      }
  
  /staff/id [GET]:
    
    Response:
      {
        "username": "Wendy",
        "password": "123",
        "role": 1
      }


# Login Service 

URL: http://localhost:5505/

  /login/staff [POST]:

    payload:
      {
        "username": "Kelly",
        "password": "123"
      }
      
    Respose:
      Kalau User dengan role staff gak ditemukan di database login
      {
        "error": "User Not Found"
      }
      Kalau Sukses
      {
        "result": "Success"
      }
      Kalau salah password
      {
        "error": "Wrong Username or Password"
      }


  /login/client [POST]:

    payload:
      {
        "username": "Dion",
        "password": "123"
      }
      
    Respose:
      Kalau User dengan role staff gak ditemukan di database login
      {
        "error": "User Not Found"
      }
      Kalau Sukses
      {
        "result": "Success"
      }
      Kalau salah password
      {
        "error": "Wrong Username or Password"
      }


# Order Service

URL: http://localhost:5507/

  /order/type [GET]:

    Respose:
      [
        {
            "id": 1,
            "type": "A"
        },
        {
            "id": 2,
            "type": "B"
        },
        {
            "id": 3,
            "type": "C"
        },
        {
            "id": 4,
            "type": "D"
        },
        {
            "id": 5,
            "type": "E"
        }
      ]


  /order [POST]:

    payload:
      {
        "client_id": 1,
        "event_type_id": 1,
        "status": 0,
        "contact": "0812",
        "date": "2023-06-20 16:59:59",
        "location": "UKP"
      }
      
    Respose:
      {
        "id": 3
      }
  
  /order [GET]:
      
    Respose:
      [
        {
            "id": 1,
            "client_id": 2,
            "event_type_id": 3,
            "status": 1,
            "contact": "0812",
            "date": "2023-06-20 16:59:59",
            "location": "UKP"
        },
        {
            "id": 2,
            "client_id": 1,
            "event_type_id": 1,
            "status": 1,
            "contact": "0812",
            "date": "2023-06-20 16:59:59",
            "location": "UKP"
        }
      ]


# Event Service

URL: http://localhost:5509/

  /event [GET]:

    Response:
    [
      {
          "id": 2,
          "order_id": 1,
          "event_type_id": 3,
          "time_start": "08:00",
          "time_end": "10:00",
          "description": "Terima Tamu",
          "pic": 1
      },
      {
          "id": 3,
          "order_id": 1,
          "event_type_id": 3,
          "time_start": "10:00",
          "time_end": "12:00",
          "description": "Nyanyi Lagu",
          "pic": 1
      },
      {
          "id": 4,
          "order_id": 1,
          "event_type_id": 3,
          "time_start": "12:00",
          "time_end": "15:00",
          "description": "Goodbye",
          "pic": 1
      },
      {
          "id": 5,
          "order_id": 2,
          "event_type_id": 1,
          "time_start": "08:00",
          "time_end": "10:00",
          "description": "Terima Tamu 2",
          "pic": 1
      },
      {
          "id": 6,
          "order_id": 2,
          "event_type_id": 1,
          "time_start": "10:00",
          "time_end": "12:00",
          "description": "Nyanyi Lagu 2",
          "pic": 1
      },
      {
          "id": 7,
          "order_id": 2,
          "event_type_id": 1,
          "time_start": "12:00",
          "time_end": "15:00",
          "description": "Goodbye 2",
          "pic": 1
      }
    ]

  /event/order_id [GET]:

    Response:
      [
        {
            "id": 2,
            "order_id": 1,
            "event_type_id": 3,
            "time_start": "08:00",
            "time_end": "10:00",
            "description": "Terima Tamu",
            "pic": 1
        },
        {
            "id": 3,
            "order_id": 1,
            "event_type_id": 3,
            "time_start": "10:00",
            "time_end": "12:00",
            "description": "Nyanyi Lagu",
            "pic": 1
        },
        {
            "id": 4,
            "order_id": 1,
            "event_type_id": 3,
            "time_start": "12:00",
            "time_end": "15:00",
            "description": "Goodbye",
            "pic": 1
        }
      ]

  /event/order_id [POST]:
  
    Payload:
      [
        {
            "event_type_id": 1,
            "time_start": "08:00",
            "time_end": "10:00",
            "description": "Terima Tamu 2",
            "pic": 1
        },
        {
            "event_type_id": 1,
            "time_start": "10:00",
            "time_end": "12:00",
            "description": "Nyanyi Lagu 2",
            "pic": 1
        },
        {
            "event_type_id": 1,
            "time_start": "12:00",
            "time_end": "15:00",
            "description": "Goodbye 2",
            "pic": 1
        }
      ]

    Response:
      {
        "result": "Success"
      }

/status/order_id [PUT]:
  
    Payload:
      {
        "status": 1
      }

      
