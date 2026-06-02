const express = require("express");
const multer = require("multer");
const path = require("path");
const fs = require("fs");
const Anthropic = require("@anthropic-ai/sdk");
const OpenAI = require("openai");

const app = express();
const PORT = process.env.PORT || 3000;

// Clients
const anthropic = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

// Middleware
app.use(express.json({ limit: "50mb" }));
app.use(express.static("public"));

// File upload setup
const storage = multer.memoryStorage();
const upload = multer({
  storage,
  limits: { fileSize: 20 * 1024 * 1024 }, // 20MB
  fileFilter: (req, file, cb) => {
    const allowed = [
      "image/jpeg","image/png","image/gif","image/webp",
      "application/pdf","text/plain","text/csv",
      "application/json","text/javascript","text/html","text/css",
      "application/msword",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ];
    if (allowed.includes(file.mimetype) || file.mimetype.startsWith("text/")) {
      cb(null, true);
    } else {
      cb(new Error("Fayl turi qo'llab-quvvatlanmaydi"));
    }
  },
});

// Helper: file to base64
function fileToBase64(buffer) {
  return buffer.toString("base64");
}

// Helper: detect if image
function isImage(mimetype) {
  return mimetype.startsWith("image/");
}

// ── Claude API ──────────────────────────────────────────────────────────────
async function callClaude(messages, files) {
  const formattedMessages = [];

  for (const msg of messages) {
    if (msg.role === "user") {
      const content = [];

      // Attach files to the last user message
      if (files && files.length > 0 && msg === messages[messages.length - 1]) {
        for (const file of files) {
          if (isImage(file.mimetype)) {
            content.push({
              type: "image",
              source: {
                type: "base64",
                media_type: file.mimetype,
                data: fileToBase64(file.buffer),
              },
            });
          } else if (file.mimetype === "application/pdf") {
            content.push({
              type: "document",
              source: {
                type: "base64",
                media_type: "application/pdf",
                data: fileToBase64(file.buffer),
              },
            });
          } else {
            // Text-based files
            const text = file.buffer.toString("utf-8");
            content.push({
              type: "text",
              text: `📎 Fayl: ${file.originalname}\n\`\`\`\n${text}\n\`\`\``,
            });
          }
        }
      }

      content.push({ type: "text", text: msg.content });
      formattedMessages.push({ role: "user", content });
    } else {
      formattedMessages.push({ role: "assistant", content: msg.content });
    }
  }

  const response = await anthropic.messages.create({
    model: "claude-sonnet-4-5",
    max_tokens: 4096,
    system:
      "Siz aqlli va foydali AI yordamchisiz. Fayllar, rasmlar, kodlar va har qanday savollar bilan yordam bera olasiz. O'zbek, rus va ingliz tillarini bilasiz.",
    messages: formattedMessages,
  });

  return response.content[0].text;
}

// ── GPT API ─────────────────────────────────────────────────────────────────
async function callGPT(messages, files) {
  const formattedMessages = [
    {
      role: "system",
      content:
        "Siz aqlli va foydali AI yordamchisiz. Fayllar, rasmlar, kodlar va har qanday savollar bilan yordam bera olasiz. O'zbek, rus va ingliz tillarini bilasiz.",
    },
  ];

  for (const msg of messages) {
    if (msg.role === "user") {
      const content = [];

      if (files && files.length > 0 && msg === messages[messages.length - 1]) {
        for (const file of files) {
          if (isImage(file.mimetype)) {
            content.push({
              type: "image_url",
              image_url: {
                url: `data:${file.mimetype};base64,${fileToBase64(file.buffer)}`,
              },
            });
          } else {
            const text = file.buffer.toString("utf-8");
            content.push({
              type: "text",
              text: `📎 Fayl: ${file.originalname}\n\`\`\`\n${text}\n\`\`\``,
            });
          }
        }
      }

      content.push({ type: "text", text: msg.content });
      formattedMessages.push({ role: "user", content });
    } else {
      formattedMessages.push({ role: "assistant", content: msg.content });
    }
  }

  const response = await openai.chat.completions.create({
    model: "gpt-4.1",
    max_tokens: 4096,
    messages: formattedMessages,
  });

  return response.choices[0].message.content;
}

// ── Routes ───────────────────────────────────────────────────────────────────

// Chat endpoint
app.post("/api/chat", upload.array("files", 5), async (req, res) => {
  try {
    const { messages, model } = req.body;
    const parsedMessages = JSON.parse(messages);
    const files = req.files || [];

    let reply;
    if (model === "claude") {
      reply = await callClaude(parsedMessages, files);
    } else {
      reply = await callGPT(parsedMessages, files);
    }

    res.json({ reply });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: err.message || "Xatolik yuz berdi" });
  }
});

// Health check
app.get("/health", (req, res) => res.json({ status: "ok" }));

app.listen(PORT, () => console.log(`✅ Server http://localhost:${PORT} da ishlamoqda`));
