"use client";

import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

// Esquema de validación del formulario con Zod
const formSchema = z.object({
  key: z.string().min(3, "La key del fragmento es requerida."), // fragment_id -> key
  text: z.string().min(10, "El contenido es muy corto."), // content -> text
  lockType: z.enum(["none", "existing", "new"]).default("none"),
  existingProductId: z.string().optional(),
  newProductName: z.string().optional(),
  newProductPrice: z.coerce.number().optional(),
  newProductImageFileId: z.string().optional(), // Added for image_file_id
}).refine(data => {
    if (data.lockType === 'existing' && !data.existingProductId) {
        return false;
    }
    return true;
}, { message: "Debes seleccionar un producto existente.", path: ["existingProductId"] })
.refine(data => {
    if (data.lockType === 'new' && (!data.newProductName || data.newProductName.length < 3)) {
        return false;
    }
    return true;
}, { message: "El nombre del nuevo producto es requerido.", path: ["newProductName"] });

type Product = { id: number; name: string; price: number; image_file_id?: string }; // Updated Product type

export function NarrativeEditor() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      key: "", // fragment_id -> key
      text: "", // content -> text
      lockType: "none",
    },
  });

  const lockType = form.watch("lockType");
  const newProductName = form.watch("newProductName");

  useEffect(() => {
    if (lockType === "existing") {
      fetch("/api/products")
        .then((res) => res.json())
        .then(setProducts);
    }
  }, [lockType]);

  async function onSubmit(values: z.infer<typeof formSchema>) {
    setIsSubmitting(true);
    
    let payload: any = {
        key: values.key, // fragment_id -> key
        text: values.text, // content -> text
        new_product_lock: null,
    };

    if (values.lockType === 'new') {
        payload.new_product_lock = {
            name: values.newProductName,
            price: values.newProductPrice || 0,
            description: `Acceso al fragmento: ${values.key}`, // Use key for description
            image_file_id: values.newProductImageFileId || null, // Include image_file_id
        };
    }
    // Note: If lockType is 'existing', we don't send unlock_product_id in the fragment payload.
    // The backend logic now handles the ShopItem's unlocks_fragment_key.
    // The frontend only needs to trigger the creation of the fragment, and if a new product is involved,
    // provide its details. The linking happens on the backend.

    try {
        const response = await fetch('/api/narrative_fragments', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Error al crear el fragmento.");
        }

        const result = await response.json();
        toast.success(`Fragmento "${result.key}" creado correctamente.`); // Use result.key
        form.reset();

    } catch (error: any) {
        toast.error(error.message);
    } finally {
        setIsSubmitting(false);
    }
  }

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader>
        <CardTitle>Editor Narrativo Unificado</CardTitle>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-8">
            <FormField
              control={form.control}
              name="key" // fragment_id -> key
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Key del Fragmento</FormLabel>
                  <FormControl>
                    <Input placeholder="ej: capitulo_1_inicio" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="text" // content -> text
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Contenido</FormLabel>
                  <FormControl>
                    <Textarea placeholder="Escribe la historia aquí..." {...field} rows={5} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="lockType"
              render={({ field }) => (
                <FormItem className="space-y-3">
                  <FormLabel>Condición de Acceso</FormLabel>
                  <FormControl>
                    <RadioGroup
                      onValueChange={field.onChange}
                      defaultValue={field.value}
                      className="flex flex-col space-y-1"
                    >
                      <FormItem className="flex items-center space-x-3 space-y-0">
                        <FormControl><RadioGroupItem value="none" /></FormControl>
                        <FormLabel className="font-normal">Sin bloqueo (Acceso Libre)</FormLabel>
                      </FormItem>
                      <FormItem className="flex items-center space-x-3 space-y-0">
                        <FormControl><RadioGroupItem value="existing" /></FormControl>
                        <FormLabel className="font-normal">Bloquear con producto existente</FormLabel>
                      </FormItem>
                      <FormItem className="flex items-center space-x-3 space-y-0">
                        <FormControl><RadioGroupItem value="new" /></FormControl>
                        <FormLabel className="font-normal">Bloquear con producto nuevo (crear al vuelo)</FormLabel>
                      </FormItem>
                    </RadioGroup>
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            {lockType === 'existing' && (
              <FormField
                control={form.control}
                name="existingProductId"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Seleccionar Producto</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Busca y selecciona un producto..." />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {products.map(p => (
                          <SelectItem key={p.id} value={String(p.id)}>
                            {p.name} (Precio: {p.price})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            )}

            {lockType === 'new' && (
              <div className="p-4 border-l-4 border-blue-500 bg-blue-50 rounded-md space-y-4">
                 <FormField
                    control={form.control}
                    name="newProductName"
                    render={({ field }) => (
                        <FormItem>
                        <FormLabel>Nombre del Nuevo Producto</FormLabel>
                        <FormControl>
                            <Input placeholder="ej: Llave del Misterio" {...field} />
                        </FormControl>
                        <FormMessage />
                        </FormItem>
                    )}
                    />
                <FormField
                    control={form.control}
                    name="newProductPrice"
                    render={({ field }) => (
                        <FormItem>
                        <FormLabel>Precio</FormLabel>
                        <FormControl>
                            <Input type="number" placeholder="100" {...field} />
                        </FormControl>
                        <FormMessage />
                        </FormItem>
                    )}
                    />
                <FormField
                    control={form.control}
                    name="newProductImageFileId"
                    render={({ field }) => (
                        <FormItem>
                        <FormLabel>ID de Archivo de Imagen (Telegram)</FormLabel>
                        <FormControl>
                            <Input placeholder="AgACAgIAAxkBAA..." {...field} />
                        </FormControl>
                        <FormMessage />
                        </FormItem>
                    )}
                    />
                <FormDescription>
                  Este fragmento se bloqueará con el producto 
                  <strong className="text-gray-800"> "{newProductName || '...'}" </strong> 
                  que se creará automáticamente al guardar.
                </FormDescription>
              </div>
            )}

            <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Guardando..." : "Guardar Fragmento"}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  );
}