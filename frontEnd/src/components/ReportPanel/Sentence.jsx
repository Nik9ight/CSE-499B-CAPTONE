import './Sentence.css';

export default function Sentence({ id, text, isActive, onClick }) {
  return (
    <span
      className={`sent${isActive ? ' active' : ''}`}
      onClick={() => onClick(id)}
    >
      {text}
    </span>
  );
}
