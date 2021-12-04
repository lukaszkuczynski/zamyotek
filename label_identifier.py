class LabelIdentifier:

    def __init__(self, label_filename):
        self.labels = self.__read_labels(label_filename)
        self.labels_inv = {v: k for k, v in self.labels.items()}

    def __read_labels(self, label_filename):
        labels = {}
        label_no = 0
        for line in open(label_filename):
            labels[label_no] = line.strip()
            label_no += 1
        return labels

    def label_for_number(self, number):
        if not number in self.labels.keys():
            raise Exception(f"Number {number} not in labels, max {max(self.labels.keys())}") 
        return self.labels[number]

    def number_for_label(self, text):
        if not text in self.labels_inv.keys():
            raise Exception(f"Label {text} not in labels")
        return int(self.labels_inv[text])

    def all_labels(self):
        return set(self.labels.values())


if __name__ == '__main__':
    filename = "/usr/local/bin/networks/SSD-Mobilenet-v2/ssd_coco_labels.txt"
    ident = LabelIdentifier(filename)
    print(ident.labels)
    print(ident.number_for_label('person'))
