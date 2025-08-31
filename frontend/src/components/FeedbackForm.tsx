import { useState } from "react";
import api from "../api";

type Props = { submissionId: string; onSubmitted: () => void };

export default function FeedbackForm({ submissionId, onSubmitted }: Props) {
  const [userId, setUserId] = useState("u_demo_user");
  const [rating, setRating] = useState(5);
  const [text, setText] = useState("");

  const submit = async () => {
    await api.feedback({ submission_id: submissionId, user_id: userId, rating, text });
    setText("");
    onSubmitted();
  };

  return (
    <div className="card">
      <div className="row" style={{ justifyContent: "space-between" }}>
        <b>Feedback</b>
      </div>
      <div className="list">
        <input placeholder="User ID" value={userId} onChange={e => setUserId(e.target.value)} />
        <input type="number" min={1} max={5} value={rating} onChange={e => setRating(Number(e.target.value))} />
        <textarea rows={3} placeholder="Your feedback" value={text} onChange={e => setText(e.target.value)} />
        <button className="btn" onClick={submit}>Submit</button>
      </div>
    </div>
  );
}
