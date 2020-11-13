package com.company;

import java.io.IOException;
import java.io.ObjectInputStream;
import java.io.ObjectOutputStream;
import java.net.Socket;
import java.util.Scanner;

public class Client {
    private Socket socket;
    private ObjectInputStream inputStream;
    private ObjectOutputStream outStream;
    private String serverIP;
    private int port;


    public Client(String serverIP, int port) {
        this.serverIP = serverIP;
        this.port = port;
        try {
            this.socket = new Socket(serverIP, port);
            this.outStream = new ObjectOutputStream(this.socket.getOutputStream());
            this.inputStream = new ObjectInputStream(this.socket.getInputStream());
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    public ObjectInputStream getInputStream() {
        return inputStream;
    }

    public ObjectOutputStream getOutStream() {
        return outStream;
    }

    public static void main(String[] args) {
        Client client = new Client("localhost", 5000);
        ObjectInputStream inputStream = client.getInputStream();
        ObjectOutputStream outputStream = client.getOutStream();
        Scanner scanner = new Scanner(System.in);
        Message message;
        String username = null;
        String action;
        String string;
        while(true){
            Payload payload = client.receive(inputStream, outputStream);
            System.out.println(payload.getMessage().getContext());
            switch (payload.getType()){
                case "login":
                    switch (payload.getRequest()) {
                        case "username":
                            username = scanner.nextLine();
                            message = new Message(username, "server", username);
                            payload = new Payload("login", "username", message);
                            client.send(payload, inputStream, outputStream);
                            break;
                        case "password":
                            String password = scanner.nextLine();
                            message = new Message(username, "server", password);
                            payload = new Payload("login", "password", message);
                            client.send(payload, inputStream, outputStream);
                            break;
                        case "OS":
                            String OS = scanner.nextLine();
                            message = new Message(username, "server", OS);
                            payload = new Payload("login", "OS", message);
                            client.send(payload, inputStream, outputStream);
                            break;
                    }
                    break;

                case "choose":
                    action = scanner.nextLine();
                    message = new Message(username, "server", action);
                    payload = new Payload("choose", "action", message);
                    System.out.println(payload.getMessage().getContext());
                    client.send(payload, inputStream, outputStream);
                    break;

                case "cmd":
                    string = scanner.nextLine();
                    message = new Message(username, "server", string);
                    payload = new Payload("cmd", "command", message);
                    client.send(payload, inputStream, outputStream);
                    break;

                case "message mode":
                    switch (payload.getRequest()){
                        case "command":
                            string = scanner.nextLine();
                            message = new Message(username, "server", string);
                            payload = new Payload("message mode", "command", message);
                            client.send(payload, inputStream, outputStream);
                            break;

                        case "send":
                            System.out.println("Who is the receiver?");
                            String receiver = scanner.nextLine();
                            System.out.println("What's the message?");
                            string = scanner.nextLine();
                            message = new Message(username, receiver, string);
                            payload = new Payload("message mode", "send", message);
                            client.send(payload, inputStream, outputStream);
                            break;

                    }
                    break;

                case "error":
                    return;
            }

        }


    }

    private void send(Payload outPayload, ObjectInputStream inputStream, ObjectOutputStream outputStream){
        try {
            outputStream.writeUnshared(outPayload);;
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private Payload receive(ObjectInputStream inputStream, ObjectOutputStream outputStream){
        Payload inPayload = null;
        try {
            inPayload = (Payload) inputStream.readObject();
        } catch (IOException e) {
            e.printStackTrace();
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        }
        return inPayload;
    }
}
