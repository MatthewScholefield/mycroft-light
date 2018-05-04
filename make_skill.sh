#!/usr/bin/env bash

eval skills_dir="~/.mycroft/skills"
dialog_dir="locale/en-us"

if [ "$#" -gt "1" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [ClassName]"
    exit 0
fi

class_name="$1"

while true; do
    if [ -z "$class_name" ]; then
        read -p "Enter skill class name (ie. AlarmSkill): " class_name
    fi
    if ! [ "${class_name##*Skill}" ]; then
        break
    fi
    echo 'Class name must end with "Skill".'
    class_name=''
done

folder_name=$(echo $class_name | sed -r 's/([A-Z])/_\L\1/g' | sed -r 's/^_//g')
skill_dir="$skills_dir/$folder_name"
mkdir -p "$skill_dir"
mkdir -p "$skill_dir/$dialog_dir"

cat << EOF > "$skill_dir/skill.py"
from mycroft import MycroftSkill, Package, intent_handler


class $class_name(MycroftSkill):
    @intent_handler('')
    def _(self, p: Package):
        p.data = {
            '': ''
        }

EOF

echo "Finished!"
echo "Wrote to $skill_dir"
