import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { Plus, Edit, Trash2, Loader2 } from "lucide-react";
import { toast } from "@/components/ui/sonner";
import apiService from "@/services/api";
import { FormFieldType } from "@/types";

interface FormKey {
  id: number;
  name: string;
  field_type: string;
  required: boolean;
  enum_values?: string[] | null;
  employer_id: number;
  created_at?: string;
  updated_at?: string;
}

const FormKeysManagement = () => {
  const [formKeys, setFormKeys] = useState<FormKey[]>([]);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingKey, setEditingKey] = useState<FormKey | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    name: "",
    field_type: "",
    required: false,
    enum_values: "",
  });

  // Get employer_id from token (no longer needed for API calls, but kept for reference)
  const getEmployerId = () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.employer_id;
      } catch (error) {
        console.error('Failed to parse token:', error);
        return null;
      }
    }
    return null;
  };

  const fetchFormKeys = async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // No need to pass employer_id anymore - it's extracted from token on backend
      const response = await apiService.getFormKeysByCompany();
      setFormKeys(response || []);
    } catch (error) {
      console.error('Failed to fetch form keys:', error);
      setError(error.message || 'Failed to fetch form keys');
      toast.error("Failed to fetch form keys", {
        description: error.message || "An unexpected error occurred.",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async () => {
    if (!formData.name || !formData.field_type) {
      toast.error("Error", {
        description: "Please fill in all required fields.",
      });
      return;
    }

    setIsSubmitting(true);

    try {
      const enum_array = formData.enum_values 
        ? formData.enum_values.split(",").map(v => v.trim()).filter(v => v)
        : null;

      const form_key_data = {
        name: formData.name,
        field_type: formData.field_type,
        required: formData.required,
        enum_values: enum_array,
        // employer_id is no longer needed - extracted from token on backend
      };

      if (editingKey) {
        const updated_key = await apiService.updateFormKey(editingKey.id, form_key_data);
        setFormKeys(formKeys.map(key => 
          key.id === editingKey.id ? updated_key : key
        ));
        toast.success("Success", {
          description: "Form key updated successfully.",
        });
      } else {
        const new_key = await apiService.createFormKey(form_key_data);
        setFormKeys([...formKeys, new_key]);
        toast.success("Success", {
          description: "Form key created successfully.",
        });
      }

      resetForm();
    } catch (error) {
      console.error('Failed to save form key:', error);
      toast.error("Error", {
        description: error.message || "Failed to save form key.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = (key: FormKey) => {
    setEditingKey(key);
    setFormData({
      name: key.name,
      field_type: key.field_type,
      required: key.required,
      enum_values: key.enum_values?.join(", ") || "",
    });
    setIsDialogOpen(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await apiService.deleteFormKey(id);
      setFormKeys(formKeys.filter(key => key.id !== id));
      toast.success("Success", {
        description: "Form key deleted successfully.",
      });
    } catch (error) {
      console.error('Failed to delete form key:', error);
      toast.error("Error", {
        description: error.message || "Failed to delete form key.",
      });
    }
  };

  const resetForm = () => {
    setFormData({
      name: "",
      field_type: "",
      required: false,
      enum_values: "",
    });
    setEditingKey(null);
    setIsDialogOpen(false);
  };

  useEffect(() => {
    fetchFormKeys();
  }, []);

  if (isLoading) {
    return (
      <div className="flex-1 space-y-8 p-8">
        <div className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin" />
          <span className="ml-2">Loading form keys...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 space-y-8 p-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <p className="text-destructive mb-4">Error: {error}</p>
            <Button onClick={fetchFormKeys}>
              Retry
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 space-y-8 p-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Form Keys Management</h1>
          <p className="text-muted-foreground">
            Manage custom form fields for job applications
          </p>
        </div>
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogTrigger asChild>
            <Button onClick={() => setEditingKey(null)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Form Key
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>
                {editingKey ? "Edit Form Key" : "Add New Form Key"}
              </DialogTitle>
              <DialogDescription>
                Create custom fields that can be attached to job applications.
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="name">Field Name</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({...formData, name: e.target.value})}
                  placeholder="e.g., Experience Years"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="fieldType">Field Type</Label>
                <Select
                  value={formData.field_type}
                  onValueChange={(value) => setFormData({...formData, field_type: value})}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select field type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="text">Text</SelectItem>
                    <SelectItem value="number">Number</SelectItem>
                    <SelectItem value="email">Email</SelectItem>
                    <SelectItem value="date">Date</SelectItem>
                    <SelectItem value="select">Select</SelectItem>
                    <SelectItem value="textarea">Textarea</SelectItem>
                    <SelectItem value="checkbox">Checkbox</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              {formData.field_type === "select" && (
                <div className="space-y-2">
                  <Label htmlFor="enum_values">Options (comma-separated)</Label>
                  <Textarea
                    id="enum_values"
                    value={formData.enum_values}
                    onChange={(e) => setFormData({...formData, enum_values: e.target.value})}
                    placeholder="Option 1, Option 2, Option 3"
                    rows={3}
                  />
                </div>
              )}
              <div className="flex items-center space-x-2">
                <Switch
                  id="required"
                  checked={formData.required}
                  onCheckedChange={(checked) => setFormData({...formData, required: checked})}
                />
                <Label htmlFor="required">Required field</Label>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={resetForm} disabled={isSubmitting}>
                Cancel
              </Button>
              <Button onClick={handleSubmit} disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    {editingKey ? "Updating..." : "Creating..."}
                  </>
                ) : (
                  editingKey ? "Update" : "Create"
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Form Keys</CardTitle>
          <CardDescription>
            Manage all custom form fields used in job applications
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Field Type</TableHead>
                <TableHead>Required</TableHead>
                <TableHead>Options</TableHead>
                <TableHead>Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {formKeys.map((key) => (
                <TableRow key={key.id}>
                  <TableCell className="font-medium">{key.name}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{key.field_type}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant={key.required ? "default" : "secondary"}>
                      {key.required ? "Yes" : "No"}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    {key.enum_values && key.enum_values.length > 0
                      ? key.enum_values.slice(0, 2).join(", ") + 
                        (key.enum_values.length > 2 ? "..." : "")
                      : "—"}
                  </TableCell>
                  <TableCell>
                    <div className="flex space-x-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleEdit(key)}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDelete(key.id)}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
};

export default FormKeysManagement;
