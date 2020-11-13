package com.company;

import java.util.ArrayList;
import java.io.*;
import java.net.*;

public class Server {

    private class User{
        private boolean isRegistered;
        private boolean isLoggedIn;
        private String username;
        private String password;
        private ArrayList<Message> receivedMesssages;
        private ArrayList<Message> sentMesssages;
        private String OS;

        public User(String username, String password, String OS) {
            this.username = username;
            this.password = password;
            this.OS = OS;
            this.isRegistered = true;
            this.isLoggedIn = true;
            this.receivedMesssages = new ArrayList<Message>();
            this.sentMesssages = new ArrayList<Message>();
        }

        public boolean isRegistered() {
            return isRegistered;
        }

        public boolean isLogined() {
            return isLoggedIn;
        }

        public void login(){
            this.isLoggedIn = true;
        }

        public void logout(){
            this.isLoggedIn = false;
        }

    }


    private ArrayList<User> users;
    private ServerSocket serverSocket;
    private int port;

    private Server(int port){
        this.port = port;
        this.users = new ArrayList<User>();
        try {
            this.serverSocket = new ServerSocket(port);
        } catch (IOException e) {
            System.out.println("Unable to create socket for the server!");
        }
    }


    public static void main(String[] args) throws IOException {
        Server server = new Server(5000);
        while (true){

            Socket socket = server.serverSocket.accept();
            final ObjectOutputStream outputStream = new ObjectOutputStream(socket.getOutputStream());
            final ObjectInputStream inputStream = new ObjectInputStream(socket.getInputStream());

            Thread thread = new Thread(){
                @Override
                public void run(){
                    User user = server.login(inputStream, outputStream);
                    if (user == null)
                        return;
                    Outer: while (true){
                        Message message = new Message("server", user.username, "Choose:" +
                                "\ncmd\nmessage mode\nlog out");
                        Payload payload = new Payload("choose", "action", message);
                        payload = server.sendAndReceive(payload, inputStream, outputStream);
                        message = payload.getMessage();
                        String type = message.getContext();
                        switch (type){
                            case "cmd":
                                message = new Message("server", user.username, "Command mode: Command?");
                                payload = new Payload("cmd", "command", message);
                                payload = server.sendAndReceive(payload, inputStream, outputStream);
                                while (!payload.getMessage().getContext().equals("back")) {
                                    Runtime runtime = Runtime.getRuntime();
                                    StringBuilder output = null;
                                    try {
                                        Process process = runtime.exec("sh -c " + payload.getMessage().getContext());
                                        BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream()));
                                        output = new StringBuilder();
                                        String line;
                                        while ((line = reader.readLine()) != null) {
                                            output.append(line + "\n");
                                        }
                                    } catch (IOException e) {
                                        e.printStackTrace();
                                    }
                                    message = new Message("server", user.username, output.toString() + "\nNext command?");
                                    payload = new Payload("cmd", "command", message);
                                    payload = server.sendAndReceive(payload, inputStream, outputStream);
                                }
                                break;


                            case "message mode":
                                message = new Message("server", user.username, "Message mode: Action?\nsend\nreceive\nunread");
                                payload = new Payload("message mode", "command", message);
                                payload = server.sendAndReceive(payload, inputStream, outputStream);
                                A: while (!payload.getMessage().getContext().equals("back")) {
                                    String action = payload.getMessage().getContext();
                                    switch (action){
                                        case "send":
                                            message = new Message("server", user.username, "Please specify your message's details!");
                                            payload = new Payload("message mode", "send", message);
                                            payload = server.sendAndReceive(payload, inputStream, outputStream);
                                            String receiver = payload.getMessage().getReceiver();
                                            User receiverUser = server.findUser(receiver);
                                            if (receiverUser == null){
                                                message = new Message("server", user.username, "Receiver has not registered yet!\n" +
                                                        "Message mode: Action?\nsend\nreceive\nunread");
                                                payload = new Payload("message mode", "command", message);
                                                payload = server.sendAndReceive(payload, inputStream, outputStream);
                                                continue A;
                                            }
                                            user.sentMesssages.add(payload.getMessage());
                                            receiverUser.receivedMesssages.add(payload.getMessage());
                                            message = new Message("server", user.username, "Message mode: Action?\nsend\nreceive\nunread");
                                            payload = new Payload("message mode", "command", message);
                                            payload = server.sendAndReceive(payload, inputStream, outputStream);
                                            break;

                                        case "receive":
                                            String context = "";
                                            for(Message message1: user.receivedMesssages){
                                                context = context + "From " + message1.getSender() + ":\n" + message1.getContext() + "\n";
                                                message1.read();
                                            }
                                            context = context + "\n";
                                            message = new Message("server", user.username, context + "Message mode: Action?\nsend\nreceive\nunread");
                                            payload = new Payload("message mode", "command", message);
                                            payload = server.sendAndReceive(payload, inputStream, outputStream);
                                            break;

                                        case "unread":
                                            String context1 = "";
                                            for(Message message1: user.receivedMesssages){
                                                if (!message1.isSeen()) {
                                                    context1 = context1 + "From " + message1.getSender() + ":\n" + message1.getContext() + "\n";
                                                    message1.read();
                                                }
                                            }
                                            context1 = context1 + "\n";
                                            message = new Message("server", user.username, context1 + "Message mode: Action?\nsend\nreceive\nunread");
                                            payload = new Payload("message mode", "command", message);
                                            payload = server.sendAndReceive(payload, inputStream, outputStream);
                                            break;

                                        default:
                                            message = new Message("server", user.username, "Unknown Action! Connection is closed!");
                                            payload = new Payload("error", "error", message);
                                            server.send(payload, inputStream, outputStream);
                                            return;
                                    }
                                }
                                break;

                            case "log out":
                                user = server.login(inputStream, outputStream);
                                if (user == null)
                                    return;
                                continue Outer;
                            default:
                                message = new Message("server", user.username, "Unknown Command! Connection is closed!");
                                payload = new Payload("error", "error", message);
                                server.send(payload, inputStream, outputStream);
                                return;
                        }
                    }
                }
            };
            thread.start();
        }
    }

    private User login(ObjectInputStream inputStream, ObjectOutputStream outputStream){
        Message message = new Message("server", "unknown", "Please Enter your username:");
        Payload payload = new Payload("login", "username", message);
        payload = sendAndReceive(payload, inputStream, outputStream);
        String username = payload.getMessage().getContext();

        message = new Message("server", username, "Please Enter your password:");
        payload = new Payload("login", "password", message);
        payload = sendAndReceive(payload, inputStream, outputStream);
        String password = payload.getMessage().getContext();
        User user = findUser(username);
        if (user == null){
            message = new Message("server", username, "Please Enter your OS:");
            payload = new Payload("login", "OS", message);
            payload = sendAndReceive(payload, inputStream, outputStream);
            String OS = payload.getMessage().getContext();
            user = new User(username, password, OS);
            users.add(user);
        } else {
            if (!user.password.equals(password)){
                message = new Message("server", username, "Password is wrong! Connection is closed!");
                payload = new Payload("error", "password", message);
                send(payload, inputStream, outputStream);
                return null;
            }
        }
        return user;


    }

    private User findUser(String username){
        for(User user: this.users){
            if (user.username.equals(username))
                return user;
        }
        return null;
    }

    private Payload sendAndReceive(Payload outPayload, ObjectInputStream inputStream, ObjectOutputStream outputStream){
        Payload inPayload = null;
        try {
            outputStream.writeUnshared(outPayload);
            inPayload = (Payload) inputStream.readObject();
        } catch (IOException e) {
            e.printStackTrace();
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        }
        return inPayload;
    }


    private void send(Payload outPayload, ObjectInputStream inputStream, ObjectOutputStream outputStream){
        try {
            outputStream.writeUnshared(outPayload);;
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

}
