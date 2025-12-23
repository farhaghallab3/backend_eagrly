/*
PRODUCT FORM UPDATE:
Change the category field from a select dropdown to a text input.
Replace this:

<select
  {...register("category", { required: "Please select a category" })}
  className={styles.select}
>
  <option value="">Select Category</option>
  {loading ? (
    <option>Loading...</option>
  ) : (
    categories.map((cat) => (
      <option key={cat.id} value={cat.id}>
        {cat.name}
      </option>
    ))
  )}
</select>

With this:

<input
  type="text"
  {...register("category", {
    required: "Please enter a category",
    minLength: { value: 2, message: "Category name must be at least 2 characters" }
  })}
  placeholder="Type category name or select from dropdown"
  className={styles.input}
  list="category-list"
/>
<datalist id="category-list">
  {categories.map((cat) => (
    <option key={cat.id} value={cat.name} />
  ))}
</datalist>

Also update the form validation to accept the new category field constraints.
*/

// Original ChatbotWidget.jsx - UPDATED VERSION
import React, { useState, useEffect } from "react";
import { FaRobot, FaTimes } from "react-icons/fa";
import { useNavigate } from "react-router-dom";
import { sendMessageToBot } from "../../../services/chatService";
import styles from "./ChatbotWidget.module.css";

const ChatbotWidget = () => {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [showAll, setShowAll] = useState({});

  const toggleChat = () => setOpen(!open);

  // Auto-load personalized recommendations on component mount
  useEffect(() => {
    if (open && messages.length === 0) {
      fetchRecommendations();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      const response = await sendMessageToBot("", true); // Send empty message with initial=true
      const botMsg = {
        role: "bot",
        content: response.reply || "",
        products: response.products || []
      };
      setMessages([botMsg]);
    } catch (err) {
      console.error("Chatbot error:", err);
      const errorMessage = err.response?.data?.reply || err.response?.data?.error || "An error occurred while fetching recommendations.";
      setMessages([{
        role: "bot",
        content: errorMessage
      }]);
    } finally {
      setLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { role: "user", content: input };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const response = await sendMessageToBot(input);
      const botMsg = {
        role: "bot",
        content: response.reply || "Here are the results:",
        products: response.recommendations || response.results || []
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      console.error("Chatbot error:", err);
      const errorMessage = err.response?.data?.reply || err.response?.data?.error || "An error occurred while contacting the server.";
      setMessages(prev => [...prev, { 
        role: "bot", 
        content: errorMessage
      }]);
    } finally {
      setLoading(false);
    }
  };

  const toggleShowAll = (messageIndex) => {
    setShowAll(prev => ({
      ...prev,
      [messageIndex]: !prev[messageIndex]
    }));
  };

  const renderBotMessage = (msg, messageIndex) => {
    if (!msg.products || msg.products.length === 0) {
      return <span>{msg.content}</span>;
    }

    const isExpanded = showAll[messageIndex] || false;
    const displayedProducts = isExpanded ? msg.products : msg.products.slice(0, 3);

    return (
      <div>
        <div style={{ marginBottom: '10px' }}>{msg.content}</div>

        {displayedProducts.map(product => (
          <div key={product.id} className={styles.productPreview}>
            <div 
              className={styles.productTitle} 
              style={{ cursor: 'pointer', color: '#007bff', textDecoration: 'underline' }}
              onClick={() => navigate(`/product/${product.id}`)}
            >
              {product.title}
            </div>
            <div className={styles.productMeta}>
              {product.seller?.first_name && `Seller: ${product.seller.first_name}`}
              {product.seller?.email && ` (${product.seller.email})`}
              {product.university && ` | University: ${product.university}`}
              {product.faculty && ` | Faculty: ${product.faculty}`}
              {product.price && ` | Price: EGP ${product.price}`}
              {product.condition && ` | Condition: ${product.condition}`}
              {product.category_name && ` | Category: ${product.category_name}`}
            </div>
          </div>
        ))}

        {msg.products.length > 3 && (
          <button
            className={styles.seeMoreBtn}
            onClick={() => toggleShowAll(messageIndex)}
          >
            {isExpanded ? "Show Less" : `See ${msg.products.length - 3} more`}
          </button>
        )}
      </div>
    );
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") sendMessage();
  };

  return (
    <div className={styles.widgetWrapper}>
      {!open && (
        <button className={styles.chatButton} onClick={toggleChat}>
          <FaRobot />
        </button>
      )}

      {open && (
        <div className={styles.chatBox}>
          <div className={styles.chatHeader}>
            AI Product Assistant
            <FaTimes style={{ cursor: "pointer" }} onClick={toggleChat} />
          </div>

          <div className={styles.chatMessages}>
            {messages.map((msg, idx) => (
              <div
                key={idx}
                className={`${styles.message} ${msg.role === "user" ? styles.user : styles.bot}`}
              >
                {msg.role === "bot" ? renderBotMessage(msg, idx) : msg.content}
              </div>
            ))}

            {loading && (
              <div className={`${styles.message} ${styles.bot}`}>
                Loading...
              </div>
            )}
          </div>

          <div className={styles.chatInput}>
            <input
              type="text"
              placeholder="Type tool name or 'show tools'..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
            />
            <button onClick={sendMessage} disabled={loading}>
              {loading ? "..." : "Send"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatbotWidget;
