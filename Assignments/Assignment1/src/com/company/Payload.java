package com.company;

import java.io.Serializable;

public class Payload implements Serializable {
    private String type;
    private String request;
    private Message message;

    public Payload(String type, String request, Message message) {
        this.type = type;
        this.request = request;
        this.message = message;
    }

    public String getType() {
        return type;
    }

    public void setType(String type) {
        this.type = type;
    }

    public String getRequest() {
        return request;
    }

    public void setRequest(String request) {
        this.request = request;
    }

    public Message getMessage() {
        return message;
    }

    public void setMessage(Message message) {
        this.message = message;
    }
}
