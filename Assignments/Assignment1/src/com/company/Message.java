package com.company;

import java.io.Serializable;

public class Message implements Serializable {
    private String sender;
    private String receiver;
    private String context;
    private boolean seen;

    public Message(String sender, String receiver, String context){
        this.sender = sender;
        this.receiver = receiver;
        this.context = context;
        this.seen = false;
    }

    public String getSender() {
        return sender;
    }

    public void setSender(String sender) {
        this.sender = sender;
    }

    public String getReceiver() {
        return receiver;
    }

    public void setReciever(String receiver) {
        this.receiver = receiver;
    }

    public String getContext() {
        return context;
    }

    public void setContext(String context) {
        this.context = context;
    }

    public void read(){
        this.seen = true;
    }

    public boolean isSeen() {
        return seen;
    }
}

