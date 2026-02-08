# Frontend Architecture Diagram

## Complete Chat Bot Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                         Frontend Application                             │
│                    (React + TypeScript + shadcn/ui)                     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
                                   │
                                   │
          ┌────────────────────────┴────────────────────────┐
          │                                                  │
          ▼                                                  ▼
┌─────────────────────┐                          ┌─────────────────────┐
│                     │                          │                     │
│   REST API Client   │                          │  WebSocket Manager  │
│   (fetch/axios)     │                          │   (Your existing    │
│                     │                          │    class reused!)   │
└─────────┬───────────┘                          └─────────┬───────────┘
          │                                                  │
          │ HTTP/REST                                        │ WebSocket
          │ Port 5050                                        │ Port 5051
          │                                                  │
          ▼                                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│                            Backend Services                              │
│                         (Flask + Python + SQLite)                       │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Hierarchy

```
<ChatBotPage>
  ├── <ChatHeader>
  │   ├── Title: "Pycelize Chat Bot"
  │   ├── Chat ID display
  │   └── Delete button
  │
  ├── <ChatMessages>  (ScrollArea)
  │   ├── <ChatMessage type="system">
  │   │   ├── <Avatar> Bot Icon
  │   │   └── <Card> Message bubble (left-aligned, gray)
  │   │
  │   ├── <ChatMessage type="user">
  │   │   ├── <Avatar> User Icon
  │   │   └── <Card> Message bubble (right-aligned, blue)
  │   │
  │   ├── <ChatMessage type="file">
  │   │   └── File attachment with download link
  │   │
  │   └── <WorkflowProgress>  (if processing)
  │       ├── <Loader2> Spinner
  │       ├── <Badge> Status
  │       ├── <Progress> Bar
  │       └── Message text
  │
  ├── <ChatInput>
  │   ├── <Button> Paperclip (file upload)
  │   ├── <Input> Text message
  │   └── <Button> Send
  │
  └── <WorkflowConfirmDialog>  (modal)
      ├── <DialogHeader> "Confirm Workflow"
      ├── Workflow steps preview
      │   └── Each step shows:
      │       - Operation name
      │       - Arguments (JSON)
      │       - Description
      └── <DialogFooter>
          ├── <Button> Cancel
          └── <Button> Confirm & Execute
```

## Data Flow

### 1. Initialize Chat

```
User Opens Page
       │
       ▼
   initChat()
       │
       ├─→ POST /chat/bot/conversations
       │        │
       │        ▼
       │   Get chat_id & welcome message
       │        │
       └────────┴─→ Store in state
                     │
                     ├─→ Display welcome message
                     └─→ Connect WebSocket
```

### 2. Send Message

```
User Types Message
       │
       ▼
   sendMessage(text)
       │
       ├─→ Add to UI (optimistic)
       │
       ├─→ POST /chat/bot/conversations/{id}/message
       │        │
       │        ▼
       │   Bot processes message
       │        │
       │        ├─→ Intent classification
       │        ├─→ Suggest workflow
       │        └─→ Return response
       │                 │
       └─────────────────┴─→ Add bot response to UI
                              │
                              ├─→ If workflow suggested:
                              │   Show confirmation dialog
                              └─→ Update pending workflow
```

### 3. Upload File

```
User Selects File
       │
       ▼
   uploadFile(file)
       │
       ├─→ Show upload progress
       │
       ├─→ POST /chat/bot/conversations/{id}/upload
       │        │
       │        ▼
       │   File saved to storage
       │        │
       │        ├─→ Bot analyzes file
       │        ├─→ Suggest workflow
       │        └─→ Return response
       │                 │
       └─────────────────┴─→ Add file message to UI
                              │
                              ├─→ Add bot response
                              └─→ Show confirmation dialog
```

### 4. Confirm Workflow

```
User Clicks "Confirm"
       │
       ▼
   confirmWorkflow(true)
       │
       ├─→ POST /chat/bot/conversations/{id}/confirm
       │        │
       │        ▼
       │   Start workflow execution
       │        │
       │        ├─→ Create workflow steps
       │        ├─→ Save to database
       │        └─→ Execute asynchronously
       │                 │
       └─────────────────┴─→ Add confirmation to UI
                              │
                              └─→ Clear pending workflow
```

### 5. Workflow Progress (WebSocket)

```
Backend Starts Workflow
       │
       ├─→ WS: workflow_started
       │        │
       │        └─→ Show progress UI
       │
       ├─→ WS: progress (multiple times)
       │        │
       │        └─→ Update progress bar
       │             └─→ Update status text
       │
       └─→ WS: workflow_completed
                │
                ├─→ Hide progress UI
                ├─→ Show success message
                └─→ Add download links
```

## State Management

### Using React Context

```
<ChatProvider>
  │
  ├─ State:
  │   ├── chatId: string
  │   ├── messages: Message[]
  │   ├── isLoading: boolean
  │   ├── pendingWorkflow: any
  │   └── workflowProgress: any
  │
  ├─ Actions:
  │   ├── setChatId(id)
  │   ├── addMessage(msg)
  │   ├── setLoading(bool)
  │   ├── setPendingWorkflow(workflow)
  │   └── setWorkflowProgress(progress)
  │
  └─ Components:
      └── <ChatBotPage>
          └── useChatContext() → access state & actions
```

### Using Zustand Store

```
useChatStore
  │
  ├─ State:
  │   ├── chatId
  │   ├── messages
  │   ├── isLoading
  │   └── pendingWorkflow
  │
  └─ Actions:
      ├── setChatId()
      ├── addMessage()
      ├── setLoading()
      └── reset()
```

## API Flow Diagram

```
┌──────────┐
│ Frontend │
└────┬─────┘
     │
     │ 1. POST /chat/bot/conversations
     ├────────────────────────────────────┐
     │                                    │
     │ ← chat_id, welcome message         │
     │                                    ▼
     │                           ┌──────────────┐
     │                           │   Backend    │
     │                           │ ChatBotService│
     │                           └──────────────┘
     │
     │ 2. POST /conversations/{id}/message
     ├────────────────────────────────────┐
     │    { message: "extract columns" }  │
     │                                    │
     │ ← bot_response, suggested_workflow │
     │    requires_confirmation: true     │
     │                                    ▼
     │                           ┌──────────────┐
     │                           │Intent        │
     │                           │Classifier    │
     │                           └──────────────┘
     │
     │ 3. POST /conversations/{id}/upload
     ├────────────────────────────────────┐
     │    file: data.xlsx                 │
     │                                    │
     │ ← file_path, download_url          │
     │    bot_response                    │
     │                                    ▼
     │                           ┌──────────────┐
     │                           │   Storage    │
     │                           │   + DB       │
     │                           └──────────────┘
     │
     │ 4. POST /conversations/{id}/confirm
     ├────────────────────────────────────┐
     │    { confirmed: true }             │
     │                                    │
     │ ← bot_response, output_files       │
     │                                    ▼
     │                           ┌──────────────┐
     │                           │ Streaming    │
     │                           │ Executor     │
     │                           └──────────────┘
     │
     │ 5. WebSocket connection
     └────────────────────────────────────┐
                                          │
          ← progress updates              ▼
          ← workflow_completed    ┌──────────────┐
                                  │  WebSocket   │
                                  │   Server     │
                                  └──────────────┘
```

## WebSocket Message Flow

```
┌──────────┐                      ┌──────────────┐
│ Frontend │                      │   Backend    │
│WebSocket │                      │  WS Server   │
│ Manager  │                      │  (Port 5051) │
└────┬─────┘                      └──────┬───────┘
     │                                   │
     │ 1. Connect                        │
     │───────────────────────────────────>
     │                                   │
     │ 2. connected                      │
     <───────────────────────────────────│
     │   { type: "connected" }           │
     │                                   │
     │                                   │
     │ 3. Workflow starts (from API)     │
     │                                   │
     │ 4. workflow_started               │
     <───────────────────────────────────│
     │   { type: "workflow_started" }    │
     │                                   │
     │ 5. progress (multiple)            │
     <───────────────────────────────────│
     │   { type: "progress",             │
     │     progress: 45 }                │
     │                                   │
     │ 6. workflow_completed             │
     <───────────────────────────────────│
     │   { type: "workflow_completed" }  │
     │                                   │
     │ 7. ping (keepalive)               │
     │───────────────────────────────────>
     │                                   │
     │ 8. pong                           │
     <───────────────────────────────────│
     │                                   │
```

## Error Handling Flow

```
API Call Fails
     │
     ├─→ Network Error?
     │   ├─ Yes → Toast: "Connection failed"
     │   └─ No → Continue
     │
     ├─→ HTTP 4xx Error?
     │   ├─ Yes → Toast: Error message from server
     │   └─ No → Continue
     │
     ├─→ HTTP 5xx Error?
     │   ├─ Yes → Toast: "Server error"
     │   └─ No → Continue
     │
     └─→ Log error to console
         └─→ Optionally report to error tracking service
```

```
WebSocket Disconnects
     │
     ├─→ Was it intentional?
     │   ├─ Yes → Do nothing
     │   └─ No → Continue
     │
     ├─→ Attempt reconnection
     │   │
     │   ├─ Try 1: Wait 1s
     │   ├─ Try 2: Wait 2s
     │   ├─ Try 3: Wait 4s
     │   ├─ Try 4: Wait 8s
     │   └─ Try 5: Wait 16s
     │       │
     │       ├─ Success → Continue
     │       └─ Fail → Show "Connection lost" message
     │                  Prompt user to refresh
```

## File Structure

```
src/
├── api/
│   └── chatbot.ts              # API client (7 endpoints)
│
├── hooks/
│   ├── useChatBot.ts           # Main bot logic
│   ├── useChatWebSocket.ts     # WebSocket connection
│   └── useWebSocketHandler.ts  # Message handler
│
├── components/
│   ├── chat/
│   │   ├── ChatMessage.tsx     # Message bubble
│   │   ├── ChatInput.tsx       # Input + upload
│   │   ├── ChatMessages.tsx    # Message container
│   │   ├── WorkflowConfirmDialog.tsx
│   │   └── WorkflowProgress.tsx
│   │
│   └── ui/                     # shadcn/ui components
│       ├── button.tsx
│       ├── input.tsx
│       ├── card.tsx
│       ├── avatar.tsx
│       ├── badge.tsx
│       ├── dialog.tsx
│       ├── progress.tsx
│       └── ...
│
├── lib/
│   ├── websocket-manager.ts   # Your existing class
│   └── utils.ts                # Utility functions
│
├── stores/  (if using Zustand)
│   └── chatStore.ts            # Global chat state
│
├── contexts/  (if using Context)
│   └── ChatContext.tsx         # Chat provider
│
└── app/
    └── chat/
        └── page.tsx            # Main chat page
```

## Quick Start Flow

```
Step 1: Setup
   │
   ├─ Install shadcn/ui components
   └─ Copy websocket-manager.ts

Step 2: API Client
   │
   └─ Copy api/chatbot.ts → All 7 endpoints ready

Step 3: Hooks
   │
   ├─ Copy useChatBot.ts → Bot interaction logic
   ├─ Copy useChatWebSocket.ts → WebSocket connection
   └─ Copy useWebSocketHandler.ts → Message handling

Step 4: Components
   │
   ├─ Copy ChatMessage.tsx
   ├─ Copy ChatInput.tsx
   ├─ Copy ChatMessages.tsx
   ├─ Copy WorkflowConfirmDialog.tsx
   └─ Copy WorkflowProgress.tsx

Step 5: Main Page
   │
   └─ Copy ChatBotPage.tsx → Complete implementation

Step 6: Test
   │
   ├─ Start backend (ports 5050 & 5051)
   ├─ Start frontend
   └─ Test all features
```

---

**All diagrams and flows are detailed in the main guide!**

See `docs/CHAT_INTEGRATE_FRONTEND.md` for complete code examples.
