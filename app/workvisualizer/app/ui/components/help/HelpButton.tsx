import React from 'react';

interface HelpIconButtonProps {
    onClick: () => void;
}

const HelpIconButton: React.FC<HelpIconButtonProps> = ({ onClick }) => {
    return (
        <div onClick={onClick} style={{
            width: '25px',
            height: '25px',
            borderRadius: '50%',
            backgroundColor: '#495057',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            color: 'white',
            fontSize: '15px',
            border: 'none',
            transition: 'background-color 0.2s',
        }}
        onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#343a40'; }}
        onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#495057'; }}
        >
            ?
        </div>
    );
};

export default HelpIconButton;
