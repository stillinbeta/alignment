import React, {Component} from 'react';

import UserAvatar from '../components/UserAvatar.js';
import SizeSelector from '../components/SizeSelector.js';
import Draggable from 'react-draggable';

import './AvatarField.css';

class AvatarField extends Component {
    static defaultProps = {
        onMoveStart: (av) => {},
        onMoveEnd: (av) => {},
        onMove: (av) => {},
        locked: true,
        background: "/default-background.png",
        backgroundHeight: 680,
        backgroundWidth: 675
    }

    constructor(props) {
        super(props);
        this.state = {
            avatarSize: props.avatarSize
        };

        this.onSizeChange = this.onSizeChange.bind(this);
    }

    onSizeChange(newSize) {
        this.setState({avatarSize: newSize});
    }

    // Move whatever avatar has just been moved to the top of the stack
    onMoveStart(userId, e, dd) {
        this.props.onMoveStart(userId);
    }

    onMove(userId, e, position) {
        const {x, y} = position;
        this.props.onMove(userId, {x, y});
    }

    render() {
        var avatars = [];
        for (var [userId, avatar] of this.props.icons) {
            avatars.push(
                    <Draggable
                onDrag={this.onMove.bind(this, avatar.get('user').id)}
                bounds="parent"
                position={avatar.get('position')}
                disabled={this.props.locked}
                key={userId}
                    >
                    <UserAvatar user={avatar.get('user')} size={this.state.avatarSize}/>
                    </Draggable>

            );
        }

        const background = {
            backgroundImage: `url(${this.props.background})`,
            height: `${this.props.backgroundHeight}px`,
            width: `${this.props.backgroundWidth}px`
        };

        return (
            <div>
                <SizeSelector value={this.state.avatarSize} user={this.props.user} min="32" max="128"
            onSizeChange={this.onSizeChange}/>
                <div id="avatar-field" style={background}>
                {avatars}
                </div>
           </div>
        );
    }
}

export default AvatarField;
